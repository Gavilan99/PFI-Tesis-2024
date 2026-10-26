import { Component, HostListener, Inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, forkJoin, of, throwError } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { isNotContinuable, isPaidTierRequired } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { Question } from '../core/models/question.model';
import { TestAttempt } from '../core/models/test-attempt.model';
import { CutStatus } from '../core/models/cut-status.model';
import { CUT_COPY } from '../core/cuts/cut-copy';
import { cutStart, hasNextCut } from '../core/cuts/cut-plan';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ProgressBarComponent } from '../shared/components/progress-bar/progress-bar.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { ScenarioItemComponent } from './scenario-item/scenario-item.component';
import { LikertItemComponent } from './likert-item/likert-item.component';
import { FeedbackFormComponent } from '../shared/components/feedback-form/feedback-form.component';
import { BetweenCutsComponent } from './between-cuts/between-cuts.component';

// CU003 — El test. One item per screen, auto-advance on select (the one
// thing rescued from the old test component), progress always visible,
// back navigation with the previous answer shown marked, keyboard
// shortcuts, save-as-you-go so a reload resumes. Dispatches to a renderer
// per questionType — adding 'ordering'/'text' later means adding a
// renderer, not touching this component.
//
// Feature 10: the test is served in three fixed cuts (40 / 90 / 145 items).
// Progress counts within the current cut, going back stops at its first
// item, and answering its last item opens the screen between cuts instead
// of closing the attempt, except on the last cut, which closes as before.
@Component({
  selector: 'app-test',
  standalone: true,
  imports: [
    PageContainerComponent,
    ProgressBarComponent,
    ErrorStateComponent,
    LoadingStateComponent,
    BrandButtonComponent,
    ScenarioItemComponent,
    LikertItemComponent,
    FeedbackFormComponent,
    BetweenCutsComponent,
  ],
  templateUrl: './test.component.html',
  styleUrl: './test.component.scss',
})
export class TestComponent implements OnInit {
  loading = true;
  error: string | null = null;
  done = false;

  questions: Question[] = [];
  currentIndex = 0;

  attemptId: string | null = null;
  private readonly selections = new Map<string, string>();

  // Where the attempt stands in the cuts; refreshed when a cut is finished,
  // since canContinue only turns true once every served item is answered.
  cut: CutStatus | null = null;
  betweenCuts = false;
  // Closing or continuing from the screen between cuts is in flight.
  busy = false;
  paidTierRequired = false;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.loadOrResume();
  }

  get currentQuestion(): Question | null {
    return this.questions[this.currentIndex] ?? null;
  }

  // Index of the current cut's first item among everything served. An
  // attempt whose served count isn't on the plan counts from the start.
  get cutStartIndex(): number {
    const start = this.cut ? cutStart(this.cut.currentCut) : 0;
    return start < this.questions.length ? start : 0;
  }

  get progressPrefix(): string {
    return this.cut ? CUT_COPY.progressPrefix(this.cut.currentCut, this.cut.cutCount) : '';
  }

  // Only on the test's first question, not at the start of each cut.
  get instruction(): string | null {
    return this.currentIndex === 0 ? CUT_COPY.instruction : null;
  }

  get progressCurrent(): number {
    return this.currentIndex - this.cutStartIndex + 1;
  }

  get progressTotal(): number {
    return this.questions.length - this.cutStartIndex;
  }

  get selectedOptionId(): string | null {
    const question = this.currentQuestion;
    return question ? this.selections.get(question.id) ?? null : null;
  }

  retry(): void {
    this.loadOrResume();
  }

  onSelect(optionId: string): void {
    const question = this.currentQuestion;
    if (!question || !this.attemptId) {
      return;
    }
    this.selections.set(question.id, optionId);
    this.api
      .submitResponse(this.attemptId, {
        questionId: question.id,
        selectedOptionId: optionId,
        freeTextResponse: null,
        orderingResponse: null,
      })
      .subscribe({
        next: () => this.advance(),
        error: () => this.fail(),
      });
  }

  // Within the current cut: the previous cuts' answers are already behind
  // the screen between cuts (and, from a closed attempt, behind its result).
  goBack(): void {
    if (this.currentIndex > this.cutStartIndex) {
      this.currentIndex--;
    }
  }

  // "Ver mi resultado" between cuts: closes the attempt in the cut it's in
  // and goes straight to the result, one click, like the end of the test.
  seeResult(): void {
    if (!this.attemptId || this.busy) {
      return;
    }
    this.busy = true;
    this.api.completeTestAttempt(this.attemptId).subscribe({
      next: () => this.router.navigateByUrl('/resultados'),
      error: () => this.fail(),
    });
  }

  continueToNextCut(): void {
    if (!this.attemptId || this.busy) {
      return;
    }
    this.busy = true;
    this.api.continueTestAttempt(this.attemptId).subscribe({
      next: (attempt) => {
        this.loading = true;
        this.resume(attempt);
      },
      error: (error: unknown) => {
        this.busy = false;
        if (isPaidTierRequired(error)) {
          this.paidTierRequired = true;
          return;
        }
        this.fail(CUT_COPY.continueError);
      },
    });
  }

  // Digits select the option at that position (1-indexed, matching the
  // small index badge each renderer shows); ArrowLeft goes back. No
  // on-screen legend — the badges are the only hint.
  @HostListener('window:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (this.loading || this.error || this.done || this.betweenCuts) {
      return;
    }
    if (event.key === 'ArrowLeft') {
      this.goBack();
      return;
    }
    const digit = Number(event.key);
    if (Number.isInteger(digit) && digit >= 1) {
      const option = this.currentQuestion?.answerOptions[digit - 1];
      if (option) {
        this.onSelect(option.id);
      }
    }
  }

  private loadOrResume(): void {
    this.loading = true;
    this.error = null;
    const userId = this.auth.currentUser?.id;
    if (!userId) {
      this.fail();
      return;
    }
    this.api.getLatestAttempt(userId).subscribe({
      next: (attempt) => {
        if (attempt && attempt.status === 'in_progress') {
          this.resume(attempt);
        } else {
          this.startNew(userId);
        }
      },
      error: () => this.fail(),
    });
  }

  // Also where a new attempt and a continued one land: whatever is served
  // and answered, the test picks up at the first unanswered item. With the
  // whole of a cut answered and a cut after it, that's the screen between
  // cuts; with the whole of the last cut answered, its last item, as before.
  private resume(attempt: TestAttempt): void {
    this.attemptId = attempt.id;
    forkJoin({
      questions: this.api.getQuestions(attempt.id),
      responses: this.api.getResponses(attempt.id),
      // An attempt from before the cuts has no cut status: it goes on as the
      // whole test did then, counting over everything served and closing at
      // its last item. Only that error: any other one, even a passing one,
      // must not turn a cut-2 attempt into one that closes at its end.
      cut: this.api
        .getCutStatus(attempt.id)
        .pipe(catchError((error: unknown) => (isNotContinuable(error) ? of(null) : throwError(() => error)))),
    }).subscribe({
      next: ({ questions, responses, cut }) => {
        this.questions = [...questions].sort((a, b) => a.displayOrder - b.displayOrder);
        this.selections.clear();
        for (const response of responses) {
          if (response.selectedOptionId) {
            this.selections.set(response.questionId, response.selectedOptionId);
          }
        }
        this.cut = cut;
        this.busy = false;
        this.paidTierRequired = false;
        const firstUnanswered = this.questions.findIndex((q) => !this.selections.has(q.id));
        this.currentIndex = firstUnanswered === -1 ? this.questions.length - 1 : firstUnanswered;
        this.betweenCuts = firstUnanswered === -1 && cut !== null && hasNextCut(cut);
        this.loading = false;
      },
      error: () => this.fail(),
    });
  }

  private startNew(userId: string): void {
    this.api.createTestAttempt(userId).subscribe({
      next: (attempt) => this.resume(attempt),
      error: () => this.fail(),
    });
  }

  private advance(): void {
    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++;
    } else if (this.cut && hasNextCut(this.cut)) {
      this.openBetweenCuts();
    } else {
      this.finish();
    }
  }

  private openBetweenCuts(): void {
    if (!this.attemptId) {
      return;
    }
    this.api.getCutStatus(this.attemptId).subscribe({
      next: (cut) => {
        this.cut = cut;
        this.betweenCuts = true;
      },
      error: () => this.fail(),
    });
  }

  private finish(): void {
    if (!this.attemptId) {
      return;
    }
    this.api.completeTestAttempt(this.attemptId).subscribe({
      next: () => {
        this.done = true;
      },
      error: () => this.fail(),
    });
  }

  private fail(message = 'No pudimos cargar el test.'): void {
    this.loading = false;
    this.busy = false;
    this.error = message;
  }
}
