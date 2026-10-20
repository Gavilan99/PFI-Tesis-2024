import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Observable, of, delay, map, shareReplay, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { Question, QuestionType } from '../models/question.model';
import { TestAttempt } from '../models/test-attempt.model';
import { NewResponseInput, TestResponse } from '../models/response.model';
import { Result } from '../models/result.model';
import { User, UpdateProfileInput, withEmptyProfile } from '../models/user.model';
import { LoginInput, RegisterInput } from '../models/auth.model';
import { SubmitFeedbackInput } from '../models/feedback.model';
import { SubmitContactMessageInput } from '../models/contact-message.model';
import { CutStatus } from '../models/cut-status.model';
import { ApiError, PAID_TIER_REQUIRED } from './api-error';
import { CUT_ENDS, cutOfServed } from '../cuts/cut-plan';

// Seeded so the error paths (duplicate email on registro, wrong credentials
// on ingreso) are testable without having to register twice by hand.
const DEMO_ACCOUNT_EMAIL = 'demo@nureon.ai';
const DEMO_ACCOUNT_PASSWORD = 'Demo1234';

// Feature 10: an account with the paid tier, so build:demo can walk the
// cuts past the first one (the backend's equivalent is a subscription given
// by scripts/grant_subscription.py). Starts with no attempts.
const PREMIUM_ACCOUNT_EMAIL = 'premium@nureon.ai';
const PREMIUM_ACCOUNT_PASSWORD = 'Demo1234';
const PREMIUM_USER_ID = 'user-premium';

// Example accuracies per cut, 0-1: the real ones come from the trained
// models' precision_by_items.json. Same shape, made-up numbers.
const MOCK_CUT_ACCURACY = [0.62, 0.71, 0.77];

const MOCK_DELAY_MS = 150;

// The backend's message for a registration without the consent.
const CONSENT_REQUIRED_MESSAGE =
  'Para crear tu cuenta tenés que aceptar la Política de privacidad y los Términos y condiciones.';

// Built by tools/build_question_fixture.py (--placeholder or --csv once the
// bank's CSV exists) into src/assets/mock/questions.sample.json. Fetched as
// a static asset, not imported, so swapping placeholder for real content is
// a file regeneration, not a rebuild. group_label is never present in this
// file on purpose — see AnswerOption's model comment.
const QUESTIONS_ASSET_URL = 'assets/mock/questions.sample.json';

interface QuestionFixtureFile {
  questions: Array<{
    id: string;
    questionType: QuestionType;
    promptText: string;
    displayOrder: number;
    options: Array<{ id: string; optionText: string; displayOrder: number }>;
  }>;
}

interface FeedbackRecord {
  id: string;
  testAttemptId: string | null;
  rating: number;
  comment: string | null;
  submittedAt: string;
}

interface ContactMessageRecord {
  id: string;
  name: string;
  email: string;
  message: string;
  submittedAt: string;
}

interface PersistedState {
  attempts: Record<string, TestAttempt>;
  responsesByAttempt: Record<string, TestResponse[]>;
  resultsByAttempt: Record<string, Result>;
  usersByEmail: Record<string, { password: string; user: User }>;
  feedback: FeedbackRecord[];
  contactMessages: ContactMessageRecord[];
  // Keyed by userId — was a single global value until Stage 7 added real
  // multi-account registration and exposed the bug: with only one implicit
  // session, nobody noticed every user's attempts lived in one shared space.
  latestAttemptIdByUser: Record<string, string>;
  // Feature 10, the fixed cuts. How many items each attempt has been served
  // (one of CUT_ENDS; an attempt persisted before this existed counts as
  // 40), which attempt continued which, and who has the paid tier.
  servedByAttempt: Record<string, number>;
  continuedFromByAttempt: Record<string, string>;
  premiumUserIds: string[];
  nextId: number;
}

const STORAGE_KEY = 'nureon_mock_api_state';

const DEMO_USER_ID = 'user-demo';
const DEMO_ATTEMPT_ID = 'attempt-demo-seed';

// Stage 10: `demo@nureon.ai` starts with a completed attempt + result
// already in place, not just an empty account — a build:demo deploy (or a
// dev poking at MockApiService) needs to reach /resultados without
// answering 40 questions first. Starting a fresh attempt from /inicio's
// "Hacer el test de nuevo" still works normally; this only seeds the
// initial state, same as DEMO_ACCOUNT_EMAIL itself.
function seedDemoAttempt(): { attempt: TestAttempt; eneatype: number } {
  const attempt: TestAttempt = {
    id: DEMO_ATTEMPT_ID,
    userId: DEMO_USER_ID,
    subjectId: null,
    tier: 'free_reduced',
    questionnaireVersion: 1,
    status: 'completed',
    startedAt: '2026-01-01T12:00:00.000Z',
    completedAt: '2026-01-01T12:15:00.000Z',
  };
  const eneatype = (Math.abs(hashCode(DEMO_ATTEMPT_ID)) % 9) + 1;
  return { attempt, eneatype };
}

function defaultState(): PersistedState {
  const { attempt, eneatype } = seedDemoAttempt();
  return {
    attempts: { [attempt.id]: attempt },
    responsesByAttempt: { [attempt.id]: [] },
    resultsByAttempt: {
      [attempt.id]: {
        id: `result-${attempt.id}`,
        testAttemptId: attempt.id,
        eneatype,
        descriptionText: `Descripción de ejemplo para el eneatipo ${eneatype}. Contenido real pendiente (Etapa 6).`,
        generatedAt: attempt.completedAt!,
      },
    },
    usersByEmail: seededAccounts(),
    feedback: [],
    contactMessages: [],
    latestAttemptIdByUser: { [DEMO_USER_ID]: attempt.id },
    servedByAttempt: { [attempt.id]: CUT_ENDS[0] },
    continuedFromByAttempt: {},
    premiumUserIds: [PREMIUM_USER_ID],
    nextId: 1,
  };
}

function seededAccounts(): PersistedState['usersByEmail'] {
  return {
    [DEMO_ACCOUNT_EMAIL]: {
      password: DEMO_ACCOUNT_PASSWORD,
      user: withEmptyProfile({ id: DEMO_USER_ID, displayName: 'Cuenta demo', email: DEMO_ACCOUNT_EMAIL }),
    },
    [PREMIUM_ACCOUNT_EMAIL]: {
      password: PREMIUM_ACCOUNT_PASSWORD,
      user: withEmptyProfile({
        id: PREMIUM_USER_ID,
        displayName: 'Cuenta premium',
        email: PREMIUM_ACCOUNT_EMAIL,
      }),
    },
  };
}

// The fixture has 40 questions, one cut's worth. Cuts 2 and 3 (50 + 55
// more) recycle them in order, under derived ids so every served item is
// still its own question with its own options: the counts on screen are the
// real ones (40 / 90 / 145) and the demo walks the same flow as production.
function servedPool(fixture: Question[]): Question[] {
  const total = CUT_ENDS[CUT_ENDS.length - 1];
  return Array.from({ length: total }, (_, index) => {
    const base = fixture[index % fixture.length];
    const round = Math.floor(index / fixture.length);
    const id = round === 0 ? base.id : `${base.id}-r${round}`;
    return {
      ...base,
      id,
      displayOrder: index + 1,
      answerOptions: base.answerOptions.map((option) => ({
        ...option,
        id: round === 0 ? option.id : `${option.id}-r${round}`,
        questionId: id,
      })),
    };
  });
}

function hashCode(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

// Persists to localStorage so a full page reload — which wipes this
// service's in-memory state, since there's no real backend behind it —
// still resumes correctly. Guarded by isPlatformBrowser: this class is also
// instantiated server-side during SSR, where localStorage doesn't exist.
@Injectable()
export class MockApiService implements ApiService {
  private readonly isBrowser: boolean;
  private state: PersistedState;
  private questions$: Observable<Question[]> | null = null;

  constructor(@Inject(PLATFORM_ID) platformId: object, private readonly http: HttpClient) {
    this.isBrowser = isPlatformBrowser(platformId);
    this.state = this.loadState();
  }

  register(input: RegisterInput): Observable<User> {
    // Same rule as the backend: no account without the consent.
    if (input.consentAccepted !== true) {
      return throwError(() => new ApiError(CONSENT_REQUIRED_MESSAGE, 'CONSENT_REQUIRED', 400));
    }
    const email = input.email.toLowerCase();
    if (this.state.usersByEmail[email]) {
      return throwError(() => new Error('Ese email ya está registrado.'));
    }
    const user = withEmptyProfile({
      id: `user-${this.state.nextId++}`,
      displayName: input.username,
      email: input.email,
    });
    this.state.usersByEmail[email] = { password: input.password, user };
    this.saveState();
    return of(user).pipe(delay(MOCK_DELAY_MS));
  }

  login(input: LoginInput): Observable<User> {
    const record = this.state.usersByEmail[input.email.toLowerCase()];
    if (!record || record.password !== input.password) {
      return throwError(() => new Error('Email o contraseña incorrectos.'));
    }
    return of(record.user).pipe(delay(MOCK_DELAY_MS));
  }

  updateProfile(userId: string, input: UpdateProfileInput): Observable<User> {
    const record = Object.values(this.state.usersByEmail).find((r) => r.user.id === userId);
    if (!record) {
      return throwError(() => new Error(`MockApiService: unknown user "${userId}"`));
    }
    record.user = { ...record.user, ...input };
    this.saveState();
    return of(record.user).pipe(delay(MOCK_DELAY_MS));
  }

  // Like the backend: the account can't log in any more and its email is
  // free again; its attempts and results stay, no longer reachable by anyone.
  deleteAccount(userId: string): Observable<void> {
    const email = Object.keys(this.state.usersByEmail).find(
      (key) => this.state.usersByEmail[key].user.id === userId,
    );
    if (!email) {
      return throwError(() => new ApiError('No se pudo autenticar la solicitud.', 'UNAUTHORIZED', 401));
    }
    delete this.state.usersByEmail[email];
    delete this.state.latestAttemptIdByUser[userId];
    this.state.premiumUserIds = this.state.premiumUserIds.filter((id) => id !== userId);
    this.saveState();
    return of(undefined).pipe(delay(MOCK_DELAY_MS));
  }

  createTestAttempt(userId: string): Observable<TestAttempt> {
    const id = `attempt-${this.state.nextId++}`;
    const attempt: TestAttempt = {
      id,
      userId,
      subjectId: null,
      tier: 'free_reduced',
      questionnaireVersion: 1,
      status: 'in_progress',
      startedAt: new Date().toISOString(),
      completedAt: null,
    };
    this.abandonInProgress(userId);
    this.state.attempts[id] = attempt;
    this.state.responsesByAttempt[id] = [];
    this.state.servedByAttempt[id] = CUT_ENDS[0];
    this.state.latestAttemptIdByUser[userId] = id;
    this.saveState();
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }

  getQuestions(attemptId: string): Observable<Question[]> {
    if (!this.questions$) {
      this.questions$ = this.http.get<QuestionFixtureFile>(QUESTIONS_ASSET_URL).pipe(
        map((fixture) =>
          servedPool(
            fixture.questions.map((q) => ({
              id: q.id,
              questionType: q.questionType,
              promptText: q.promptText,
              displayOrder: q.displayOrder,
              answerOptions: q.options.map((o) => ({
                id: o.id,
                questionId: q.id,
                optionText: o.optionText,
                displayOrder: o.displayOrder,
              })),
            })),
          ),
        ),
        shareReplay(1),
      );
    }
    // Everything served so far, like the backend: 40, 90 or 145 items.
    return this.questions$.pipe(map((pool) => pool.slice(0, this.served(attemptId))));
  }

  submitResponse(attemptId: string, response: NewResponseInput): Observable<TestResponse> {
    const attempt = this.state.attempts[attemptId];
    if (!attempt) {
      return throwError(() => new Error(`MockApiService: unknown attempt "${attemptId}"`));
    }
    const full: TestResponse = {
      id: `response-${this.state.nextId++}`,
      testAttemptId: attemptId,
      questionId: response.questionId,
      selectedOptionId: response.selectedOptionId,
      freeTextResponse: response.freeTextResponse,
      orderingResponse: response.orderingResponse,
      answeredAt: new Date().toISOString(),
    };
    const responses = this.state.responsesByAttempt[attemptId] ?? [];
    this.state.responsesByAttempt[attemptId] = responses;
    // Upsert: re-answering a question (e.g. after going back) replaces its
    // previous response instead of accumulating duplicates.
    const existingIndex = responses.findIndex((r) => r.questionId === response.questionId);
    if (existingIndex >= 0) {
      responses[existingIndex] = full;
    } else {
      responses.push(full);
    }
    this.saveState();
    return of(full).pipe(delay(MOCK_DELAY_MS));
  }

  getResponses(attemptId: string): Observable<TestResponse[]> {
    return of(this.state.responsesByAttempt[attemptId] ?? []).pipe(delay(MOCK_DELAY_MS));
  }

  completeTestAttempt(attemptId: string): Observable<TestAttempt> {
    const attempt = this.state.attempts[attemptId];
    if (!attempt) {
      return throwError(() => new Error(`MockApiService: unknown attempt "${attemptId}"`));
    }
    attempt.status = 'completed';
    attempt.completedAt = new Date().toISOString();

    // Deterministic from the attempt id, just so repeated dev testing of the
    // same attempt doesn't jump to a different eneatype on every call.
    const eneatype = (Math.abs(hashCode(attemptId)) % 9) + 1;
    this.state.resultsByAttempt[attemptId] = {
      id: `result-${attemptId}`,
      testAttemptId: attemptId,
      eneatype,
      descriptionText: `Descripción de ejemplo para el eneatipo ${eneatype}. Contenido real pendiente (Etapa 6).`,
      generatedAt: new Date().toISOString(),
    };
    this.saveState();
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }

  // Same rules, in the same order, as the backend's continue route: state
  // first, the tier only when the rest allows it.
  continueTestAttempt(attemptId: string): Observable<TestAttempt> {
    const attempt = this.state.attempts[attemptId];
    if (!attempt) {
      return throwError(() => new ApiError('El intento no existe.', 'ATTEMPT_NOT_FOUND', 404));
    }
    const blocked = this.continuationBlock(attempt);
    if (blocked) {
      return throwError(() => blocked);
    }
    const nextServed = CUT_ENDS[cutOfServed(this.served(attemptId))];
    if (attempt.status === 'in_progress') {
      attempt.tier = 'paid_full';
      this.state.servedByAttempt[attemptId] = nextServed;
      this.saveState();
      return of(attempt).pipe(delay(MOCK_DELAY_MS));
    }
    const userId = attempt.userId!;
    this.abandonInProgress(userId);
    const id = `attempt-${this.state.nextId++}`;
    const continued: TestAttempt = {
      ...attempt,
      id,
      tier: 'paid_full',
      status: 'in_progress',
      startedAt: new Date().toISOString(),
      completedAt: null,
    };
    this.state.attempts[id] = continued;
    this.state.responsesByAttempt[id] = (this.state.responsesByAttempt[attemptId] ?? []).map((r) => ({
      ...r,
      id: `response-${this.state.nextId++}`,
      testAttemptId: id,
    }));
    this.state.servedByAttempt[id] = nextServed;
    this.state.continuedFromByAttempt[id] = attemptId;
    this.state.latestAttemptIdByUser[userId] = id;
    this.saveState();
    return of(continued).pipe(delay(MOCK_DELAY_MS));
  }

  getCutStatus(attemptId: string): Observable<CutStatus> {
    const attempt = this.state.attempts[attemptId];
    if (!attempt) {
      return throwError(() => new ApiError('El intento no existe.', 'ATTEMPT_NOT_FOUND', 404));
    }
    const served = this.served(attemptId);
    const cut = cutOfServed(served);
    const isLast = cut >= CUT_ENDS.length;
    const status: CutStatus = {
      currentCut: cut,
      cutCount: CUT_ENDS.length,
      servedItems: served,
      answeredItems: this.answered(attemptId),
      nextCutItems: isLast ? null : CUT_ENDS[cut] - served,
      canContinue: this.continuationBlock(attempt) === null,
      currentCutAccuracy: MOCK_CUT_ACCURACY[cut - 1],
      nextCutAccuracy: isLast ? null : MOCK_CUT_ACCURACY[cut],
      continuedByAttemptId: this.continuedBy(attemptId),
    };
    return of(status).pipe(delay(MOCK_DELAY_MS));
  }

  getResult(attemptId: string): Observable<Result> {
    const result = this.state.resultsByAttempt[attemptId];
    if (!result) {
      return throwError(() => new Error(`MockApiService: no result for attempt "${attemptId}"`));
    }
    return of(result).pipe(delay(MOCK_DELAY_MS));
  }

  getLatestAttempt(userId: string): Observable<TestAttempt | null> {
    const latestId = this.state.latestAttemptIdByUser[userId];
    const attempt = latestId ? this.state.attempts[latestId] ?? null : null;
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }

  getAttempt(attemptId: string): Observable<TestAttempt | null> {
    return of(this.state.attempts[attemptId] ?? null).pipe(delay(MOCK_DELAY_MS));
  }

  getAttemptHistory(userId: string): Observable<TestAttempt[]> {
    const attempts = Object.values(this.state.attempts)
      .filter((a) => a.userId === userId)
      .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime());
    return of(attempts).pipe(delay(MOCK_DELAY_MS));
  }

  submitFeedback(input: SubmitFeedbackInput): Observable<void> {
    this.state.feedback.push({
      id: `feedback-${this.state.nextId++}`,
      testAttemptId: input.testAttemptId,
      rating: input.rating,
      comment: input.comment,
      submittedAt: new Date().toISOString(),
    });
    this.saveState();
    return of(undefined).pipe(delay(MOCK_DELAY_MS));
  }

  submitContactMessage(input: SubmitContactMessageInput): Observable<void> {
    this.state.contactMessages.push({
      id: `contact-${this.state.nextId++}`,
      name: input.name,
      email: input.email,
      message: input.message,
      submittedAt: new Date().toISOString(),
    });
    this.saveState();
    return of(undefined).pipe(delay(MOCK_DELAY_MS));
  }

  private served(attemptId: string): number {
    return this.state.servedByAttempt[attemptId] ?? CUT_ENDS[0];
  }

  private answered(attemptId: string): number {
    return (this.state.responsesByAttempt[attemptId] ?? []).filter((r) => r.selectedOptionId).length;
  }

  private continuedBy(attemptId: string): string | null {
    const entry = Object.entries(this.state.continuedFromByAttempt).find(([, from]) => from === attemptId);
    return entry ? entry[0] : null;
  }

  private abandonInProgress(userId: string): void {
    for (const attempt of Object.values(this.state.attempts)) {
      if (attempt.userId === userId && attempt.status === 'in_progress') {
        attempt.status = 'abandoned';
      }
    }
  }

  private latestCompletedId(userId: string): string | null {
    const completed = Object.values(this.state.attempts)
      .filter((a) => a.userId === userId && a.status === 'completed')
      .sort((a, b) => new Date(b.completedAt!).getTime() - new Date(a.completedAt!).getTime());
    return completed[0]?.id ?? null;
  }

  // Why `attempt` can't go on to the next cut, or null if it can: what
  // canContinue reports and what continueTestAttempt rejects with. Same
  // codes as the backend; one message for the 409s, which the screens never
  // show (they have their own text for any error but the paid tier).
  private continuationBlock(attempt: TestAttempt): ApiError | null {
    const served = this.served(attempt.id);
    const conflict = (code: string) => new ApiError('Este intento no se puede seguir.', code, 409);
    if (attempt.status === 'abandoned') {
      return conflict('ATTEMPT_NOT_CONTINUABLE');
    }
    if (cutOfServed(served) >= CUT_ENDS.length) {
      return conflict('LAST_CUT_REACHED');
    }
    if (this.answered(attempt.id) < served) {
      return conflict('CUT_INCOMPLETE');
    }
    if (attempt.status === 'completed') {
      if (this.continuedBy(attempt.id)) {
        return conflict('ATTEMPT_ALREADY_CONTINUED');
      }
      if (this.latestCompletedId(attempt.userId!) !== attempt.id) {
        return conflict('ATTEMPT_NOT_CONTINUABLE');
      }
    }
    if (!this.state.premiumUserIds.includes(attempt.userId!)) {
      return new ApiError('Para seguir con más preguntas necesitás una suscripción activa.', PAID_TIER_REQUIRED, 402);
    }
    return null;
  }

  private loadState(): PersistedState {
    if (!this.isBrowser) {
      return defaultState();
    }
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return defaultState();
      }
      const persisted = JSON.parse(raw) as Partial<PersistedState>;
      const defaults = defaultState();
      // A state saved before an account was seeded still gets it.
      return {
        ...defaults,
        ...persisted,
        usersByEmail: { ...seededAccounts(), ...persisted.usersByEmail },
        premiumUserIds: defaults.premiumUserIds,
      };
    } catch {
      return defaultState();
    }
  }

  private saveState(): void {
    if (!this.isBrowser) {
      return;
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state));
    } catch {
      // Storage full/unavailable (private browsing, quota) — the mock keeps
      // working in-memory for the rest of this session, it just won't
      // survive a reload.
    }
  }
}
