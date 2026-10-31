import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Observable, Subject, of, throwError } from 'rxjs';
import { ResultadosComponent } from './resultados.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError, PAID_TIER_REQUIRED } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { CutStatus } from '../core/models/cut-status.model';
import { TestAttempt } from '../core/models/test-attempt.model';
import { PersonalizedDescription } from '../core/models/result.model';
import { ENEATYPE_CONTENT } from './eneatype-content';

const attempt: TestAttempt = {
  id: 'attempt-1',
  userId: 'user-1',
  subjectId: null,
  tier: 'free_reduced',
  questionnaireVersion: 1,
  status: 'completed',
  startedAt: '2026-10-01T12:00:00Z',
  completedAt: '2026-10-01T12:20:00Z',
};

const cut: CutStatus = {
  currentCut: 1,
  cutCount: 3,
  servedItems: 40,
  answeredItems: 40,
  nextCutItems: 50,
  canContinue: true,
  currentCutAccuracy: 0.62,
  nextCutAccuracy: 0.71,
  continuedByAttemptId: null,
};

describe('ResultadosComponent, continuing from the result', () => {
  function create(continueResult: Observable<TestAttempt>) {
    const api: Partial<ApiService> = {
      getLatestAttempt: () => of(attempt),
      getResult: () =>
        of({ id: 'r-1', testAttemptId: attempt.id, eneatype: 3, descriptionText: '', generatedAt: attempt.completedAt! }),
      getCutStatus: () => of(cut),
      getAttemptHistory: () => of([attempt]),
      continueTestAttempt: () => continueResult,
      // The plans text carries "Pasar a premium", which shows the plan's price.
      getSubscription: () =>
        of({ active: false, currentPeriodEnd: null, planPrice: 4999, planCurrency: 'ARS', planDays: 30 }),
    };
    TestBed.configureTestingModule({
      imports: [ResultadosComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: { currentUser: { id: 'user-1', accountType: null } } },
      ],
    });
    const fixture = TestBed.createComponent(ResultadosComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('keeps the result on screen and shows a failed "Seguir" inside the block', () => {
    const fixture = create(
      throwError(() => new ApiError('Este test ya se siguió en otro intento.', 'ATTEMPT_ALREADY_CONTINUED', 409)),
    );
    const page = fixture.componentInstance;

    page.continueFromResult();
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(page.error).toBeNull();
    expect(page.eneatype).toBe(3);
    expect(element.querySelector('.refine__error')?.textContent).toContain('Este test ya se siguió en otro intento.');
  });

  it('turns the block into the plans text when the paid tier is missing', () => {
    const fixture = create(
      throwError(() => new ApiError('Para seguir necesitás una suscripción activa.', PAID_TIER_REQUIRED, 402)),
    );
    const page = fixture.componentInstance;

    page.continueFromResult();
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(page.refine?.canContinue).toBeFalse();
    expect(element.querySelector('.refine__error')).toBeNull();
    expect(element.querySelector('.refine__plans')).not.toBeNull();
  });
});

describe('ResultadosComponent, personalized description (Feature 18)', () => {
  const paidAttempt: TestAttempt = { ...attempt, tier: 'paid_full' };
  const result = {
    id: 'r-1',
    testAttemptId: attempt.id,
    eneatype: 3,
    descriptionText: '',
    generatedAt: attempt.completedAt!,
  };
  const genericContent = ENEATYPE_CONTENT[3];

  function nothing(status: PersonalizedDescription['status']): PersonalizedDescription {
    return { status, strengths: null, tensions: null, growth: null, stress: null };
  }

  function create(overrides: Partial<ApiService>, attemptToUse: TestAttempt = paidAttempt) {
    const api: Partial<ApiService> = {
      getLatestAttempt: () => of(attemptToUse),
      getResult: () => of(result),
      getCutStatus: () => of(cut),
      getAttemptHistory: () => of([attemptToUse]),
      ...overrides,
    };
    TestBed.configureTestingModule({
      imports: [ResultadosComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: { currentUser: { id: 'user-1', accountType: null } } },
      ],
    });
    const fixture = TestBed.createComponent(ResultadosComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('replaces the four sections and shows the personalization line', () => {
    const personalized: PersonalizedDescription = {
      status: 'personalized',
      strengths: ['Fortaleza personalizada 1', 'Fortaleza personalizada 2'],
      tensions: ['Tensión personalizada 1', 'Tensión personalizada 2'],
      growth: 'Crecimiento personalizado',
      stress: 'Estrés personalizado',
    };
    const fixture = create({ getPersonalizedDescription: () => of(personalized) });
    const page = fixture.componentInstance;
    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain('Fortaleza personalizada 1');
    expect(element.textContent).toContain('Tensión personalizada 1');
    expect(element.textContent).toContain('Crecimiento personalizado');
    expect(element.textContent).toContain('Estrés personalizado');
    expect(element.textContent).toContain('adaptadas a tu perfil');
    expect(page.personalizedAnnouncement).toBe('Tu resultado se personalizó según tu perfil.');
  });

  it('leaves a section generic when its personalized field is null or an empty list', () => {
    const personalized: PersonalizedDescription = {
      status: 'personalized',
      strengths: [],
      tensions: ['Tensión personalizada 1'],
      growth: null,
      stress: 'Estrés personalizado',
    };
    const fixture = create({ getPersonalizedDescription: () => of(personalized) });
    const page = fixture.componentInstance;

    expect(page.strengths).toEqual(genericContent.strengths);
    expect(page.tensions).toEqual(['Tensión personalizada 1']);
    expect(page.growthText).toBe(genericContent.growth);
    expect(page.stressText).toBe('Estrés personalizado');
  });

  it('shows the profile_missing invitation with a link to the profile and the generic content', () => {
    const fixture = create({ getPersonalizedDescription: () => of(nothing('profile_missing')) });
    const page = fixture.componentInstance;
    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).toContain('Completá tu tipo de cuenta');
    expect(element.querySelector('a')?.getAttribute('href')).toBe('/perfil');
    expect(page.strengths).toEqual(genericContent.strengths);
    expect(page.tensions).toEqual(genericContent.tensions);
  });

  (['not_in_plan', 'unavailable'] as const).forEach((status) => {
    it(`shows the generic content with no message for status "${status}"`, () => {
      const fixture = create({ getPersonalizedDescription: () => of(nothing(status)) });
      const page = fixture.componentInstance;
      const element = fixture.nativeElement as HTMLElement;

      expect(element.textContent).not.toContain('adaptadas a tu perfil');
      expect(element.textContent).not.toContain('Completá tu tipo de cuenta');
      expect(page.strengths).toEqual(genericContent.strengths);
      expect(page.growthText).toBe(genericContent.growth);
    });
  });

  it('shows the generic content with no message on a network error', () => {
    const fixture = create({ getPersonalizedDescription: () => throwError(() => new Error('network error')) });
    const page = fixture.componentInstance;
    const element = fixture.nativeElement as HTMLElement;

    expect(element.textContent).not.toContain('adaptadas a tu perfil');
    expect(element.textContent).not.toContain('Completá tu tipo de cuenta');
    expect(page.strengths).toEqual(genericContent.strengths);
  });

  it('never calls getPersonalizedDescription on the free plan and renders as before', () => {
    const getPersonalizedDescription = jasmine.createSpy('getPersonalizedDescription');
    const fixture = create({ getPersonalizedDescription }, attempt);
    const page = fixture.componentInstance;
    const element = fixture.nativeElement as HTMLElement;

    expect(getPersonalizedDescription).not.toHaveBeenCalled();
    expect(element.textContent).not.toContain('Personalizando');
    expect(page.strengths).toEqual(genericContent.strengths);
  });

  it('shows the discreet indicator while getPersonalizedDescription is in flight', () => {
    const pending = new Subject<PersonalizedDescription>();
    const fixture = create({ getPersonalizedDescription: () => pending.asObservable() });
    const page = fixture.componentInstance;
    const element = fixture.nativeElement as HTMLElement;

    expect(page.personalizing).toBeTrue();
    expect(element.textContent).toContain('Personalizando según tu perfil…');

    pending.next(nothing('not_in_plan'));
    pending.complete();
    fixture.detectChanges();

    expect(page.personalizing).toBeFalse();
  });
});
