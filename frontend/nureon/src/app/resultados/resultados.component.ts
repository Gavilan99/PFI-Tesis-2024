import { Component, DestroyRef, Inject, OnInit } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Observable, Subscription, catchError, forkJoin, map, of, switchMap } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError, isPaidTierRequired } from '../core/services/api-error';
import { CutStatus } from '../core/models/cut-status.model';
import { CUT_COPY } from '../core/cuts/cut-copy';
import { hasNextCut } from '../core/cuts/cut-plan';
import { AuthService } from '../core/services/auth.service';
import { AttemptTier, TestAttempt } from '../core/models/test-attempt.model';
import { AccountType } from '../core/models/user.model';
import { PersonalizedDescription } from '../core/models/result.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { EnneagramDiagramComponent, ENEATYPE_STRUCTURE } from './enneagram-diagram/enneagram-diagram.component';
import { FreemiumInfoDialogComponent } from './freemium-info-dialog/freemium-info-dialog.component';
import { RefineResultComponent } from './refine-result/refine-result.component';
import { ENEATYPE_CONTENT, EneatypeContent, FRAMING_TEXT } from './eneatype-content';

// Feature 18 — the one-line announcement for the aria-live region, said once
// per load when the personalized description actually replaces something.
const PERSONALIZED_ANNOUNCEMENT = 'Tu resultado se personalizó según tu perfil.';

// CU004 — layered reading, top to bottom: eneatype + name, one-line summary,
// core motivation, strengths/tensions, wings, then (only then) the blurred
// premium content. No classifier confidence signal shown — that's an open
// point of the plan, not a call this component makes on its own.
//
// Doubles as /resultados (latest completed attempt, fresh off the test) and
// /resultados/:attemptId (a specific past attempt, RF08 history, Stage 7) —
// same layered reading either way, only which attempt differs.
//
// Feature 10: below the reading, if the attempt has a next cut and hasn't
// been continued, a block offers to refine the result with it. The answers
// already given are kept: continuing a closed attempt makes a new one that
// carries them, and this result stays in the history.
@Component({
  selector: 'app-resultados',
  standalone: true,
  imports: [
    RouterLink,
    NgTemplateOutlet,
    PageContainerComponent,
    ErrorStateComponent,
    LoadingStateComponent,
    BrandButtonComponent,
    EnneagramDiagramComponent,
    FreemiumInfoDialogComponent,
    RefineResultComponent,
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
  private refineSubscription: Subscription | null = null;
  private loadedAttemptId: string | null = null;

  // See FreemiumInfoDialogComponent for what "Desbloquear mi perfil
  // completo" (RF09/RF10) actually opens.
  showFreemiumInfo = false;

  // The "afinar tu resultado" block: null when it doesn't show. Loaded after
  // the result and apart from it, so a failure here only hides the block.
  refine: { status: CutStatus; canContinue: boolean } | null = null;
  continuing = false;
  // A failed "Seguir", shown inside the block: the result stays on screen.
  refineError: string | null = null;

  // Feature 18 — the paid plan's personalized version of strengths, tensions,
  // growth and stress, loaded apart from the result and never blocking it.
  // Only a network error leaves this null; not_in_plan/unavailable still set
  // it to the full response (all four fields null), same visible effect
  // since every getter below falls back to the generic content either way.
  // Reset on every load() so returning from /perfil asks again.
  private personalizedSubscription: Subscription | null = null;
  personalizing = false;
  private personalized: PersonalizedDescription | null = null;
  // Said once via aria-live when the personalized sections actually land;
  // null the rest of the time so the region stays empty.
  personalizedAnnouncement: string | null = null;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
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

  // Each section falls back to its generic eneatype-content.ts version on
  // its own — an empty list or a blank paragraph never replaces a section,
  // even when the other three did.
  get strengths(): string[] {
    const list = this.personalized?.strengths;
    return list && list.length > 0 ? list : this.content?.strengths ?? [];
  }

  get tensions(): string[] {
    const list = this.personalized?.tensions;
    return list && list.length > 0 ? list : this.content?.tensions ?? [];
  }

  get growthText(): string | undefined {
    return this.personalized?.growth || this.content?.growth;
  }

  get stressText(): string | undefined {
    return this.personalized?.stress || this.content?.stress;
  }

  private get usesPersonalizedContent(): boolean {
    const p = this.personalized;
    return !!p && (!!(p.strengths && p.strengths.length) || !!(p.tensions && p.tensions.length) || !!p.growth || !!p.stress);
  }

  // The short "adapted to your profile" line and its link to /perfil: only
  // once the personalized sections actually replaced something, not just
  // because the status said 'personalized'.
  get showPersonalizedNote(): boolean {
    return this.personalized?.status === 'personalized' && this.usesPersonalizedContent;
  }

  get showProfileMissingNotice(): boolean {
    return this.personalized?.status === 'profile_missing';
  }

  retry(): void {
    this.load();
  }

  // Continues the closed attempt into a new one (its answers come along) and
  // resumes it in /test, at the first item of the next cut.
  continueFromResult(): void {
    const attemptId = this.loadedAttemptId;
    if (!attemptId || this.continuing || !this.refine?.canContinue) {
      return;
    }
    this.continuing = true;
    this.refineError = null;
    this.api
      .continueTestAttempt(attemptId)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => this.router.navigateByUrl('/test'),
        error: (error: unknown) => {
          this.continuing = false;
          if (isPaidTierRequired(error) && this.refine) {
            this.refine = { ...this.refine, canContinue: false };
            return;
          }
          // The backend's own message when there is one (e.g. "Este test ya
          // se siguió en otro intento." from a second tab).
          this.refineError = error instanceof ApiError ? error.message : CUT_COPY.continueError;
        },
      });
  }

  // Where "Pasar a premium" comes back to from Mercado Pago: this result.
  get returnPath(): string {
    return this.loadedAttemptId ? `/resultados/${this.loadedAttemptId}` : '/resultados';
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
    this.refineSubscription?.unsubscribe();
    this.refine = null;
    this.refineError = null;
    this.continuing = false;
    this.loadedAttemptId = null;
    this.personalizedSubscription?.unsubscribe();
    this.personalizing = false;
    this.personalized = null;
    this.personalizedAnnouncement = null;

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
          this.loadedAttemptId = loaded.attempt.id;
          this.loading = false;
          this.loadRefine(loaded.attempt);
          this.loadPersonalizedDescription(loaded.attempt);
        },
        error: () => this.fail(),
      });
  }

  // Feature 18 — only asked for the paid tier, and apart from the result.
  // A network error leaves `personalized` null; not_in_plan/unavailable
  // still land here as a full response (all four fields null) — either way
  // the getters below fall back to the generic content.
  private loadPersonalizedDescription(attempt: TestAttempt): void {
    if (attempt.tier !== 'paid_full') {
      return;
    }
    this.personalizing = true;
    this.personalizedSubscription = this.api
      .getPersonalizedDescription(attempt.id)
      .pipe(
        catchError(() => of(null)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((description) => {
        this.personalizing = false;
        this.personalized = description;
        if (this.showPersonalizedNote) {
          this.personalizedAnnouncement = PERSONALIZED_ANNOUNCEMENT;
        }
      });
  }

  // canContinue alone can't tell "no paid tier" from the other reasons a
  // closed attempt can't go on, and the frontend has no tier of its own to
  // ask. The other reasons this block can meet are an attempt that isn't the
  // person's latest closed one (opened from the history) and one closed with
  // items unanswered (only the mock's seeded attempt): neither can ever be
  // continued, so they show no block at all.
  private loadRefine(attempt: TestAttempt): void {
    const userId = this.auth.currentUser?.id;
    if (!userId) {
      return;
    }
    this.refineSubscription?.unsubscribe();
    this.refineSubscription = forkJoin({
      status: this.api.getCutStatus(attempt.id),
      history: this.api.getAttemptHistory(userId),
    })
      .pipe(
        catchError(() => of(null)),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((loaded) => {
        if (!loaded || loaded.status.continuedByAttemptId !== null || !hasNextCut(loaded.status)) {
          return;
        }
        const { status } = loaded;
        if (
          !status.canContinue &&
          (latestCompletedId(loaded.history) !== attempt.id || status.answeredItems < status.servedItems)
        ) {
          return;
        }
        this.refine = { status: loaded.status, canContinue: loaded.status.canContinue };
      });
  }

  private fail(): void {
    this.loading = false;
    this.error = 'No pudimos cargar tu resultado.';
  }
}

// Same order as the backend's "latest closed attempt" (completedAt, then id,
// newest first): the only closed attempt that can be continued.
function latestCompletedId(attempts: TestAttempt[]): string | null {
  const completed = attempts
    .filter((a) => a.status === 'completed' && a.completedAt)
    .sort(
      (a, b) =>
        new Date(b.completedAt!).getTime() - new Date(a.completedAt!).getTime() || (b.id > a.id ? 1 : b.id < a.id ? -1 : 0),
    );
  return completed[0]?.id ?? null;
}
