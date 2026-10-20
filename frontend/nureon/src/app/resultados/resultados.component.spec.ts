import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Observable, of, throwError } from 'rxjs';
import { ResultadosComponent } from './resultados.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError, PAID_TIER_REQUIRED } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { CutStatus } from '../core/models/cut-status.model';
import { TestAttempt } from '../core/models/test-attempt.model';

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
