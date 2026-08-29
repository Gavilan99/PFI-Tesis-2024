import { Component, HostListener, Inject, OnInit } from '@angular/core';
import { forkJoin } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { Question } from '../core/models/question.model';
import { TestAttempt } from '../core/models/test-attempt.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ProgressBarComponent } from '../shared/components/progress-bar/progress-bar.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { ScenarioItemComponent } from './scenario-item/scenario-item.component';
import { LikertItemComponent } from './likert-item/likert-item.component';

// CU003 — El test. One item per screen, auto-advance on select (the one
// thing rescued from the old test component), progress always visible,
// back navigation with the previous answer shown marked, keyboard
// shortcuts, save-as-you-go so a reload resumes. Dispatches to a renderer
// per questionType — adding 'ordering'/'text' later means adding a
// renderer, not touching this component.
@Component({
  selector: 'app-test',
  standalone: true,
  imports: [
    PageContainerComponent,
    ProgressBarComponent,
    ErrorStateComponent,
    BrandButtonComponent,
    ScenarioItemComponent,
    LikertItemComponent,
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

  private attemptId: string | null = null;
  private readonly selections = new Map<string, string>();

  constructor(@Inject(API_SERVICE) private readonly api: ApiService) {}

  ngOnInit(): void {
    this.loadOrResume();
  }

  get currentQuestion(): Question | null {
    return this.questions[this.currentIndex] ?? null;
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

  goBack(): void {
    if (this.currentIndex > 0) {
      this.currentIndex--;
    }
  }

  // Digits select the option at that position (1-indexed, matching the
  // small index badge each renderer shows); ArrowLeft goes back. No
  // on-screen legend — the badges are the only hint.
  @HostListener('window:keydown', ['$event'])
  onKeydown(event: KeyboardEvent): void {
    if (this.loading || this.error || this.done) {
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
    this.api.getLatestAttempt().subscribe({
      next: (attempt) => {
        if (attempt && attempt.status === 'in_progress') {
          this.resume(attempt);
        } else {
          this.startNew();
        }
      },
      error: () => this.fail(),
    });
  }

  private resume(attempt: TestAttempt): void {
    this.attemptId = attempt.id;
    forkJoin({
      questions: this.api.getQuestions(attempt.id),
      responses: this.api.getResponses(attempt.id),
    }).subscribe({
      next: ({ questions, responses }) => {
        this.questions = [...questions].sort((a, b) => a.displayOrder - b.displayOrder);
        this.selections.clear();
        for (const response of responses) {
          if (response.selectedOptionId) {
            this.selections.set(response.questionId, response.selectedOptionId);
          }
        }
        const firstUnanswered = this.questions.findIndex((q) => !this.selections.has(q.id));
        this.currentIndex = firstUnanswered === -1 ? this.questions.length - 1 : firstUnanswered;
        this.loading = false;
      },
      error: () => this.fail(),
    });
  }

  private startNew(): void {
    this.api.createTestAttempt().subscribe({
      next: (attempt) => {
        this.attemptId = attempt.id;
        this.api.getQuestions(attempt.id).subscribe({
          next: (questions) => {
            this.questions = [...questions].sort((a, b) => a.displayOrder - b.displayOrder);
            this.currentIndex = 0;
            this.loading = false;
          },
          error: () => this.fail(),
        });
      },
      error: () => this.fail(),
    });
  }

  private advance(): void {
    if (this.currentIndex < this.questions.length - 1) {
      this.currentIndex++;
    } else {
      this.finish();
    }
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

  private fail(): void {
    this.loading = false;
    this.error = 'No pudimos cargar el test.';
  }
}
