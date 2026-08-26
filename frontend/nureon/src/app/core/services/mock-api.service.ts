import { Injectable } from '@angular/core';
import { Observable, of, delay, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { Question } from '../models/question.model';
import { TestAttempt } from '../models/test-attempt.model';
import { NewResponseInput, TestResponse } from '../models/response.model';
import { Result } from '../models/result.model';

// In-memory fixture, not the real Question Bank v1 content — that lands in
// Stage 5 once the CSV companion is available. Just enough variety (both
// question types Question Bank v1 actually uses) to exercise the skeleton
// end to end: 3 scenario items (3 options) + 2 Likert items (5 ordered
// options), one pair per grouping system where it's easy to tell apart.
const MOCK_QUESTIONS: Question[] = [
  {
    id: 'q1',
    groupingSystem: 'Centros de Inteligencia',
    questionType: 'scenario',
    promptText: 'Ante un problema inesperado en el trabajo, tu primer impulso es...',
    version: 1,
    isActive: true,
    displayOrder: 1,
    createdAt: '2026-01-01T00:00:00.000Z',
    answerOptions: [
      { id: 'q1-a', questionId: 'q1', optionText: 'Actuar de inmediato, ya pensaré después.', groupLabel: 'Cuerpo', displayOrder: 1 },
      { id: 'q1-b', questionId: 'q1', optionText: 'Detenerme a sentir qué me genera la situación.', groupLabel: 'Corazón', displayOrder: 2 },
      { id: 'q1-c', questionId: 'q1', optionText: 'Analizar todas las opciones antes de mover un dedo.', groupLabel: 'Mente', displayOrder: 3 },
    ],
  },
  {
    id: 'q2',
    groupingSystem: 'Conjunto de Relaciones Objetales',
    questionType: 'scenario',
    promptText: 'Cuando alguien cercano se aleja sin explicación, lo que más te moviliza es...',
    version: 1,
    isActive: true,
    displayOrder: 2,
    createdAt: '2026-01-01T00:00:00.000Z',
    answerOptions: [
      { id: 'q2-a', questionId: 'q2', optionText: 'Buscar la manera de acercarme de nuevo.', groupLabel: 'Apego', displayOrder: 1 },
      { id: 'q2-b', questionId: 'q2', optionText: 'Sentir que algo se rompió y no sé cómo arreglarlo.', groupLabel: 'Frustración', displayOrder: 2 },
      { id: 'q2-c', questionId: 'q2', optionText: 'Convencerme de que no lo necesitaba tanto.', groupLabel: 'Rechazo', displayOrder: 3 },
    ],
  },
  {
    id: 'q3',
    groupingSystem: 'Conjunto Armónico',
    questionType: 'scenario',
    promptText: 'Frente a una crítica inesperada, tu reacción más habitual es...',
    version: 1,
    isActive: true,
    displayOrder: 3,
    createdAt: '2026-01-01T00:00:00.000Z',
    answerOptions: [
      { id: 'q3-a', questionId: 'q3', optionText: 'Buscarle el lado bueno y seguir adelante.', groupLabel: 'Positiva', displayOrder: 1 },
      { id: 'q3-b', questionId: 'q3', optionText: 'Ponerme a resolverlo de manera práctica.', groupLabel: 'Competente', displayOrder: 2 },
      { id: 'q3-c', questionId: 'q3', optionText: 'Reaccionar fuerte antes de calmarme.', groupLabel: 'Reactiva', displayOrder: 3 },
    ],
  },
  {
    id: 'q4',
    groupingSystem: 'Conjunto Horneviano',
    questionType: 'multiple_choice',
    promptText: 'Me cuesta decir que no cuando alguien me pide ayuda.',
    version: 1,
    isActive: true,
    displayOrder: 4,
    createdAt: '2026-01-01T00:00:00.000Z',
    answerOptions: [
      { id: 'q4-1', questionId: 'q4', optionText: 'Totalmente en desacuerdo', groupLabel: 'Complaciente', displayOrder: 1 },
      { id: 'q4-2', questionId: 'q4', optionText: 'En desacuerdo', groupLabel: 'Complaciente', displayOrder: 2 },
      { id: 'q4-3', questionId: 'q4', optionText: 'Neutral', groupLabel: 'Complaciente', displayOrder: 3 },
      { id: 'q4-4', questionId: 'q4', optionText: 'De acuerdo', groupLabel: 'Complaciente', displayOrder: 4 },
      { id: 'q4-5', questionId: 'q4', optionText: 'Totalmente de acuerdo', groupLabel: 'Complaciente', displayOrder: 5 },
    ],
  },
  {
    id: 'q5',
    groupingSystem: 'Centros de Inteligencia',
    questionType: 'multiple_choice',
    promptText: 'Suelo confiar más en lo que pienso que en lo que siento.',
    version: 1,
    isActive: true,
    displayOrder: 5,
    createdAt: '2026-01-01T00:00:00.000Z',
    answerOptions: [
      { id: 'q5-1', questionId: 'q5', optionText: 'Totalmente en desacuerdo', groupLabel: 'Mente', displayOrder: 1 },
      { id: 'q5-2', questionId: 'q5', optionText: 'En desacuerdo', groupLabel: 'Mente', displayOrder: 2 },
      { id: 'q5-3', questionId: 'q5', optionText: 'Neutral', groupLabel: 'Mente', displayOrder: 3 },
      { id: 'q5-4', questionId: 'q5', optionText: 'De acuerdo', groupLabel: 'Mente', displayOrder: 4 },
      { id: 'q5-5', questionId: 'q5', optionText: 'Totalmente de acuerdo', groupLabel: 'Mente', displayOrder: 5 },
    ],
  },
];

function hashCode(value: string): number {
  let hash = 0;
  for (let i = 0; i < value.length; i++) {
    hash = (hash << 5) - hash + value.charCodeAt(i);
    hash |= 0;
  }
  return hash;
}

const MOCK_DELAY_MS = 150;

@Injectable()
export class MockApiService implements ApiService {
  private readonly attempts = new Map<string, TestAttempt>();
  private readonly responsesByAttempt = new Map<string, TestResponse[]>();
  private readonly resultsByAttempt = new Map<string, Result>();
  private latestAttemptId: string | null = null;
  private nextId = 1;

  createTestAttempt(): Observable<TestAttempt> {
    const id = `attempt-${this.nextId++}`;
    const attempt: TestAttempt = {
      id,
      userId: 'mock-user',
      subjectId: null,
      tier: 'free_reduced',
      questionnaireVersion: 1,
      status: 'in_progress',
      startedAt: new Date().toISOString(),
      completedAt: null,
    };
    this.attempts.set(id, attempt);
    this.responsesByAttempt.set(id, []);
    this.latestAttemptId = id;
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }

  getQuestions(_attemptId: string): Observable<Question[]> {
    return of(MOCK_QUESTIONS).pipe(delay(MOCK_DELAY_MS));
  }

  submitResponse(attemptId: string, response: NewResponseInput): Observable<TestResponse> {
    const attempt = this.attempts.get(attemptId);
    if (!attempt) {
      return throwError(() => new Error(`MockApiService: unknown attempt "${attemptId}"`));
    }
    const full: TestResponse = {
      id: `response-${this.nextId++}`,
      testAttemptId: attemptId,
      questionId: response.questionId,
      selectedOptionId: response.selectedOptionId,
      freeTextResponse: response.freeTextResponse,
      orderingResponse: response.orderingResponse,
      answeredAt: new Date().toISOString(),
    };
    this.responsesByAttempt.get(attemptId)?.push(full);
    return of(full).pipe(delay(MOCK_DELAY_MS));
  }

  completeTestAttempt(attemptId: string): Observable<TestAttempt> {
    const attempt = this.attempts.get(attemptId);
    if (!attempt) {
      return throwError(() => new Error(`MockApiService: unknown attempt "${attemptId}"`));
    }
    attempt.status = 'completed';
    attempt.completedAt = new Date().toISOString();

    // Deterministic from the attempt id, just so repeated dev testing of the
    // same attempt doesn't jump to a different eneatype on every call.
    const eneatype = (Math.abs(hashCode(attemptId)) % 9) + 1;
    this.resultsByAttempt.set(attemptId, {
      id: `result-${attemptId}`,
      testAttemptId: attemptId,
      eneatype,
      descriptionText: `Descripción de ejemplo para el eneatipo ${eneatype}. Contenido real pendiente (Etapa 6).`,
      generatedAt: new Date().toISOString(),
    });
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }

  getResult(attemptId: string): Observable<Result> {
    const result = this.resultsByAttempt.get(attemptId);
    if (!result) {
      return throwError(() => new Error(`MockApiService: no result for attempt "${attemptId}"`));
    }
    return of(result).pipe(delay(MOCK_DELAY_MS));
  }

  getLatestAttempt(): Observable<TestAttempt | null> {
    const attempt = this.latestAttemptId ? this.attempts.get(this.latestAttemptId) ?? null : null;
    return of(attempt).pipe(delay(MOCK_DELAY_MS));
  }
}
