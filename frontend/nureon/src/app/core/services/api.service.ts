import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import { Question } from '../models/question.model';
import { TestAttempt } from '../models/test-attempt.model';
import { NewResponseInput, TestResponse } from '../models/response.model';
import { Result } from '../models/result.model';
import { User } from '../models/user.model';
import { LoginInput, RegisterInput } from '../models/auth.model';

// Frontend-facing contract only — see PDR — NureonAI Data Model for the full
// DB schema. Components depend on this interface and the API_SERVICE token,
// never on MockApiService or HttpApiService directly, so swapping the mock
// for the real backend later touches only the provider wiring in
// app.module.ts, not any component.
export interface ApiService {
  // CU001/CU002 — register()/login() reject with an Error whose message is
  // meant to be shown inline in the form (e.g. "Ese email ya está
  // registrado."), never via alert(). Callers don't flip AuthService
  // themselves on success — Cognito replaces this whole path later, and
  // components shouldn't need to change when it does.
  register(input: RegisterInput): Observable<User>;
  login(input: LoginInput): Observable<User>;

  createTestAttempt(): Observable<TestAttempt>;
  getQuestions(attemptId: string): Observable<Question[]>;
  submitResponse(attemptId: string, response: NewResponseInput): Observable<TestResponse>;
  completeTestAttempt(attemptId: string): Observable<TestAttempt>;
  getResult(attemptId: string): Observable<Result>;
  // Most recent attempt for the current session, or null if none exists yet.
  // Drives the user-journey state machine (UserJourneyStateService).
  getLatestAttempt(): Observable<TestAttempt | null>;
}

export const API_SERVICE = new InjectionToken<ApiService>('API_SERVICE');
