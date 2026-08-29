import { Component, Inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { forkJoin } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { AuthService } from '../core/services/auth.service';
import { TestAttempt } from '../core/models/test-attempt.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { ProgressBarComponent } from '../shared/components/progress-bar/progress-bar.component';

type InicioState = 'no-attempts' | 'in-progress' | 'completed';

// The session's starting point (RF03) and where the Stage 2 user-journey
// state machine finally pays off: the primary action is decided by the
// account's state, not hardcoded. Fetches the attempt directly rather than
// through UserJourneyStateService — the "in-progress" branch also needs the
// attempt id and an answered/total count for the progress readout, and
// state$ only returns the four-way classification, not the attempt itself.
@Component({
  selector: 'app-inicio',
  standalone: true,
  imports: [
    PageContainerComponent,
    LoadingStateComponent,
    ErrorStateComponent,
    BrandButtonComponent,
    ProgressBarComponent,
  ],
  templateUrl: './inicio.component.html',
  styleUrl: './inicio.component.scss',
})
export class InicioComponent implements OnInit {
  loading = true;
  error: string | null = null;
  state: InicioState = 'no-attempts';
  answered = 0;
  total = 0;
  startingOver = false;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  get displayName(): string {
    return this.auth.currentUser?.displayName ?? '';
  }

  retry(): void {
    this.load();
  }

  // Creating a new attempt makes it the user's latest (MockApiService
  // overwrites latestAttemptIdByUser on create), so navigating to /test
  // right after resumes THIS attempt from question 1 — no separate
  // "abandon" step needed for the one being left behind.
  startOver(): void {
    const userId = this.auth.currentUser?.id;
    if (!userId || this.startingOver) {
      return;
    }
    this.startingOver = true;
    this.api.createTestAttempt(userId).subscribe({
      next: () => this.router.navigateByUrl('/test'),
      error: () => {
        this.startingOver = false;
        this.error = 'No pudimos empezar un test nuevo.';
      },
    });
  }

  private load(): void {
    this.loading = true;
    this.error = null;
    const userId = this.auth.currentUser?.id;
    if (!userId) {
      this.fail();
      return;
    }
    this.api.getLatestAttempt(userId).subscribe({
      next: (attempt) => {
        if (!attempt) {
          this.state = 'no-attempts';
          this.loading = false;
          return;
        }
        if (attempt.status === 'completed') {
          this.state = 'completed';
          this.loading = false;
          return;
        }
        // 'in_progress' and 'abandoned' both resume the same way — see
        // UserJourneyStateService's comment on the same simplification.
        this.state = 'in-progress';
        this.loadProgress(attempt);
      },
      error: () => this.fail(),
    });
  }

  private loadProgress(attempt: TestAttempt): void {
    forkJoin({
      questions: this.api.getQuestions(attempt.id),
      responses: this.api.getResponses(attempt.id),
    }).subscribe({
      next: ({ questions, responses }) => {
        this.total = questions.length;
        this.answered = responses.length;
        this.loading = false;
      },
      error: () => this.fail(),
    });
  }

  private fail(): void {
    this.loading = false;
    this.error = 'No pudimos cargar tu estado.';
  }
}
