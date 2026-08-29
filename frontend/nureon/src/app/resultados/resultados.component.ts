import { Component, Inject, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Observable, of } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { AuthService } from '../core/services/auth.service';
import { AttemptTier, TestAttempt } from '../core/models/test-attempt.model';
import { AccountType } from '../core/models/user.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { EnneagramDiagramComponent, ENEATYPE_STRUCTURE } from './enneagram-diagram/enneagram-diagram.component';
import { ENEATYPE_CONTENT, EneatypeContent, FRAMING_TEXT } from './eneatype-content';

// CU004 — layered reading, top to bottom: eneatype + name, one-line summary,
// core motivation, strengths/tensions, wings, then (only then) the blurred
// premium content. No classifier confidence signal shown — that's an open
// point of the plan, not a call this component makes on its own.
//
// Doubles as /resultados (latest completed attempt, fresh off the test) and
// /resultados/:attemptId (a specific past attempt, RF08 history, Stage 7) —
// same layered reading either way, only which attempt differs.
@Component({
  selector: 'app-resultados',
  standalone: true,
  imports: [
    PageContainerComponent,
    ErrorStateComponent,
    LoadingStateComponent,
    BrandButtonComponent,
    EnneagramDiagramComponent,
  ],
  templateUrl: './resultados.component.html',
  styleUrl: './resultados.component.scss',
})
export class ResultadosComponent implements OnInit {
  loading = true;
  error: string | null = null;
  eneatype: number | null = null;
  private tier: AttemptTier | null = null;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly route: ActivatedRoute,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  get content(): EneatypeContent | null {
    return this.eneatype ? ENEATYPE_CONTENT[this.eneatype] : null;
  }

  // RF09/RF10 encuadre slot: reads the logged-in user's own accountType now
  // that Stage 7 collects it in the profile. Falls back to 'individual' for
  // an account that hasn't set it yet, same as before Stage 7 existed.
  get encuadre(): AccountType {
    return this.auth.currentUser?.accountType ?? 'individual';
  }

  get framingIntro(): string | null {
    return FRAMING_TEXT[this.encuadre].intro ?? FRAMING_TEXT.individual.intro;
  }

  get wings(): EneatypeContent[] {
    if (!this.eneatype) {
      return [];
    }
    return ENEATYPE_STRUCTURE[this.eneatype].wings.map((n) => ENEATYPE_CONTENT[n]);
  }

  get isPaid(): boolean {
    return this.tier === 'paid_full';
  }

  retry(): void {
    this.load();
  }

  private load(): void {
    this.loading = true;
    this.error = null;

    const attemptId = this.route.snapshot.paramMap.get('attemptId');
    let attempt$: Observable<TestAttempt | null>;
    if (attemptId) {
      attempt$ = this.api.getAttempt(attemptId);
    } else {
      const userId = this.auth.currentUser?.id;
      attempt$ = userId ? this.api.getLatestAttempt(userId) : of(null);
    }

    attempt$.subscribe({
      next: (attempt) => {
        if (!attempt || attempt.status !== 'completed') {
          this.fail();
          return;
        }
        this.tier = attempt.tier;
        this.api.getResult(attempt.id).subscribe({
          next: (result) => {
            this.eneatype = result.eneatype;
            this.loading = false;
          },
          error: () => this.fail(),
        });
      },
      error: () => this.fail(),
    });
  }

  private fail(): void {
    this.loading = false;
    this.error = 'No pudimos cargar tu resultado.';
  }
}
