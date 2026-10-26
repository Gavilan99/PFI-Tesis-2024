import { InjectionToken } from '@angular/core';
import { Observable } from 'rxjs';
import { Question } from '../models/question.model';
import { TestAttempt } from '../models/test-attempt.model';
import { NewResponseInput, TestResponse } from '../models/response.model';
import { Result } from '../models/result.model';
import { User, UpdateProfileInput } from '../models/user.model';
import { LoginInput, RegisterInput } from '../models/auth.model';
import { SubmitFeedbackInput } from '../models/feedback.model';
import { SubmitContactMessageInput } from '../models/contact-message.model';
import { CutStatus } from '../models/cut-status.model';
import { CheckoutSession, PaymentConfirmation, Subscription } from '../models/subscription.model';

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
  // RF07 — profile edits. userId is explicit (unlike register/login, there's
  // no session token standing in for it yet).
  updateProfile(userId: string, input: UpdateProfileInput): Observable<User>;
  // Ley 25.326 right of deletion (PA-7): deletes the account. What
  // identifies the person is erased; answers, results and demographics stay,
  // anonymous. userId is explicit for the same reason as updateProfile.
  // The caller ends the session afterwards.
  deleteAccount(userId: string): Observable<void>;

  // userId is explicit on every attempt-scoping method below (createTestAttempt,
  // getLatestAttempt, getAttemptHistory) for the same reason as updateProfile:
  // there's no session token standing in for "whose attempts these are" yet.
  // A real backend would derive it from the auth token instead of a param.
  createTestAttempt(userId: string): Observable<TestAttempt>;
  // Contract decision: the whole subset (~40 items) arrives in one call when
  // the attempt is created, not one question at a time — the progress bar
  // can say "7 de 40" for real, and going back costs no request.
  getQuestions(attemptId: string): Observable<Question[]>;
  submitResponse(attemptId: string, response: NewResponseInput): Observable<TestResponse>;
  // Responses already recorded for this attempt — resuming a closed-and-
  // reopened test needs this to know which questions are already answered
  // and what was selected, without re-deriving it from anything else.
  getResponses(attemptId: string): Observable<TestResponse[]>;
  completeTestAttempt(attemptId: string): Observable<TestAttempt>;
  // The test is served in three fixed, nested cuts (40 / 90 / 145 items).
  // Serves the next cut and answers the attempt the test goes on in: the
  // same one if it was in progress, or a new one linked to it if it was
  // closed (its answers come along, its result stays). Rejects with an
  // ApiError whose code is PAID_TIER_REQUIRED when the account's tier
  // doesn't include that cut (see api-error.ts).
  continueTestAttempt(attemptId: string): Observable<TestAttempt>;
  // Where the attempt stands in the cuts, in any status: for the screen
  // between cuts and the result screen.
  getCutStatus(attemptId: string): Observable<CutStatus>;
  getResult(attemptId: string): Observable<Result>;
  // Most recent attempt for this user, or null if none exists yet. Drives the
  // user-journey state machine (UserJourneyStateService).
  getLatestAttempt(userId: string): Observable<TestAttempt | null>;
  // A specific attempt by id — /resultados/:attemptId (history, RF08) needs
  // this instead of "latest" once the user has more than one.
  getAttempt(attemptId: string): Observable<TestAttempt | null>;
  // Every attempt this user has ever made, newest first — full history, per
  // the PDR's "every attempt preserved, never overwritten."
  getAttemptHistory(userId: string): Observable<TestAttempt[]>;

  // RF06 — never surfaced back to the user; fire-and-forget from the client's
  // point of view.
  submitFeedback(input: SubmitFeedbackInput): Observable<void>;

  // /contacto (Stage 10) — same fire-and-forget shape as submitFeedback.
  submitContactMessage(input: SubmitContactMessageInput): Observable<void>;

  // Feature 6 — the full plan through Mercado Pago. The account comes from
  // the session; nothing here carries a price or a tier.
  // The plan's state and the price to show before paying.
  getSubscription(): Observable<Subscription>;
  // Where to send the buyer. Rejects with ALREADY_SUBSCRIBED (409) while the
  // plan is active.
  startCheckout(): Observable<CheckoutSession>;
  // Back from Mercado Pago with ?payment_id=…: the backend reads the payment
  // from Mercado Pago and, approved, records it. Rejects with
  // PAYMENT_NOT_FOUND (404) for a payment that isn't this account's.
  confirmPayment(paymentId: string): Observable<PaymentConfirmation>;
}

export const API_SERVICE = new InjectionToken<ApiService>('API_SERVICE');
