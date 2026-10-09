import { Component, DestroyRef, Inject, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute } from '@angular/router';
import { Observable, Subscription, map, of, switchMap } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { AuthService } from '../core/services/auth.service';
import { AttemptTier, TestAttempt } from '../core/models/test-attempt.model';
import { AccountType } from '../core/models/user.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { EnneagramDiagramComponent, ENEATYPE_STRUCTURE } from './enneagram-diagram/enneagram-diagram.component';
import { FreemiumInfoDialogComponent } from './freemium-info-dialog/freemium-info-dialog.component';
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
    FreemiumInfoDialogComponent,
  ],
  templateUrl: './resultados.component.html',
  styleUrl: './resultados.component.scss',
})
export class ResultadosComponent implements OnInit {
  // Drawn under the blur instead of content.growth/content.stress when the
  // tier doesn't include them: blurred text only hides from the eye, and
  // anyone can read it from devtools. Roughly the same length as the real
  // paragraphs so the locked block keeps its shape.
  readonly lockedPlaceholder = [
    'Este párrafo es un relleno. En el perfil completo, acá aparece cómo se expresa tu eneatipo cuando estás en tu mejor momento.',
    'Este párrafo también es un relleno. En el perfil completo, acá aparece cómo se expresa tu eneatipo en situaciones de presión.',
  ];

  loading = true;
  error: string | null = null;
  eneatype: number | null = null;
  private tier: AttemptTier | null = null;
  // From the route on every param change: the router reuses this component
  // when going from /resultados/A to /resultados/B, so reading the snapshot
  // once in ngOnInit kept showing A under B's URL.
  private attemptId: string | null = null;
  private loadSubscription: Subscription | null = null;

  // See FreemiumInfoDialogComponent for what "Desbloquear mi perfil
  // completo" (RF09/RF10) actually opens.
  showFreemiumInfo = false;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly route: ActivatedRoute,
    private readonly destroyRef: DestroyRef,
  ) {}

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      this.attemptId = params.get('attemptId');
      this.load();
    });
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

  openFreemiumInfo(): void {
    this.showFreemiumInfo = true;
  }

  closeFreemiumInfo(): void {
    this.showFreemiumInfo = false;
  }

  private load(): void {
    // A load still in flight for the previous attempt must not land on top
    // of this one.
    this.loadSubscription?.unsubscribe();
    this.loading = true;
    this.error = null;
    this.eneatype = null;
    this.tier = null;
    this.showFreemiumInfo = false;

    let attempt$: Observable<TestAttempt | null>;
    if (this.attemptId) {
      attempt$ = this.api.getAttempt(this.attemptId);
    } else {
      const userId = this.auth.currentUser?.id;
      attempt$ = userId ? this.api.getLatestAttempt(userId) : of(null);
    }

    this.loadSubscription = attempt$
      .pipe(
        switchMap((attempt) =>
          !attempt || attempt.status !== 'completed'
            ? of(null)
            : this.api.getResult(attempt.id).pipe(map((result) => ({ attempt, result }))),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (loaded) => {
          if (!loaded) {
            this.fail();
            return;
          }
          this.tier = loaded.attempt.tier;
          this.eneatype = loaded.result.eneatype;
          this.loading = false;
        },
        error: () => this.fail(),
      });
  }

  private fail(): void {
    this.loading = false;
    this.error = 'No pudimos cargar tu resultado.';
  }
}
