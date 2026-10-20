import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { TestComponent } from './test.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { Question } from '../core/models/question.model';
import { TestAttempt } from '../core/models/test-attempt.model';

const attempt: TestAttempt = {
  id: 'attempt-1',
  userId: 'user-1',
  subjectId: null,
  tier: 'free_reduced',
  questionnaireVersion: 0,
  status: 'in_progress',
  startedAt: '2026-10-01T12:00:00Z',
  completedAt: null,
};

function questions(count: number): Question[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `q-${i + 1}`,
    questionType: 'scenario',
    promptText: `Pregunta ${i + 1}`,
    displayOrder: i + 1,
    answerOptions: [1, 2, 3].map((n) => ({
      id: `q-${i + 1}-o${n}`,
      questionId: `q-${i + 1}`,
      optionText: `Opción ${n}`,
      displayOrder: n,
    })),
  }));
}

describe('TestComponent', () => {
  function create(cutError: ApiError) {
    const api: Partial<ApiService> = {
      getLatestAttempt: () => of(attempt),
      getQuestions: () => of(questions(20)),
      getResponses: () => of([]),
      getCutStatus: () => throwError(() => cutError),
    };
    TestBed.configureTestingModule({
      imports: [TestComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: { currentUser: { id: 'user-1' } } },
      ],
    });
    const fixture = TestBed.createComponent(TestComponent);
    fixture.detectChanges();
    return fixture.componentInstance;
  }

  // Served before the cuts existed (20 or 60 items): the backend has no cut
  // status for it, and the test goes on as it did then.
  it('resumes an attempt from before the cuts, counting over everything served', () => {
    const test = create(new ApiError('Este intento ya no se puede seguir.', 'ATTEMPT_NOT_CONTINUABLE', 409));

    expect(test.error).toBeNull();
    expect(test.cut).toBeNull();
    expect(test.betweenCuts).toBeFalse();
    expect(test.progressPrefix).toBe('');
    expect(test.progressCurrent).toBe(1);
    expect(test.progressTotal).toBe(20);
  });

  // Any other failure must not fall back to that: an attempt in cut 2 would
  // otherwise close at its last item instead of showing the screen between cuts.
  it('shows the error state when the cut status fails for any other reason', () => {
    const test = create(new ApiError('No pudimos conectarnos con el servidor.', 'NETWORK_ERROR', 0));

    expect(test.error).toBe('No pudimos cargar el test.');
  });
});
