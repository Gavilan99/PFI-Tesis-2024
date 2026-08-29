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

// Seeded so the error paths (duplicate email on registro, wrong credentials
// on ingreso) are testable without having to register twice by hand.
const DEMO_ACCOUNT_EMAIL = 'demo@nureon.ai';
const DEMO_ACCOUNT_PASSWORD = 'Demo1234';

const MOCK_DELAY_MS = 150;

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

interface PersistedState {
  attempts: Record<string, TestAttempt>;
  responsesByAttempt: Record<string, TestResponse[]>;
  resultsByAttempt: Record<string, Result>;
  usersByEmail: Record<string, { password: string; user: User }>;
  feedback: FeedbackRecord[];
  // Keyed by userId — was a single global value until Stage 7 added real
  // multi-account registration and exposed the bug: with only one implicit
  // session, nobody noticed every user's attempts lived in one shared space.
  latestAttemptIdByUser: Record<string, string>;
  nextId: number;
}

const STORAGE_KEY = 'nureon_mock_api_state';

function defaultState(): PersistedState {
  return {
    attempts: {},
    responsesByAttempt: {},
    resultsByAttempt: {},
    usersByEmail: {
      [DEMO_ACCOUNT_EMAIL]: {
        password: DEMO_ACCOUNT_PASSWORD,
        user: withEmptyProfile({
          id: 'user-demo',
          displayName: 'Cuenta demo',
          email: DEMO_ACCOUNT_EMAIL,
        }),
      },
    },
    feedback: [],
    latestAttemptIdByUser: {},
    nextId: 1,
  };
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
    this.state.attempts[id] = attempt;
    this.state.responsesByAttempt[id] = [];
    this.state.latestAttemptIdByUser[userId] = id;
    this.saveState();
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }

  getQuestions(_attemptId: string): Observable<Question[]> {
    if (!this.questions$) {
      this.questions$ = this.http.get<QuestionFixtureFile>(QUESTIONS_ASSET_URL).pipe(
        map((fixture) =>
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
        shareReplay(1),
      );
    }
    return this.questions$;
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

  private loadState(): PersistedState {
    if (!this.isBrowser) {
      return defaultState();
    }
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return defaultState();
      }
      return { ...defaultState(), ...JSON.parse(raw) };
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
