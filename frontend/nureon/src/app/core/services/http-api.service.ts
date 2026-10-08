import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, map, of, tap, throwError } from 'rxjs';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';
import { SessionTokenStore } from '../auth/session-token.store';
import { Question } from '../models/question.model';
import { TestAttempt } from '../models/test-attempt.model';
import { NewResponseInput, TestResponse } from '../models/response.model';
import { Result } from '../models/result.model';
import { User, UpdateProfileInput } from '../models/user.model';
import { LoginInput, RegisterInput } from '../models/auth.model';
import { SubmitFeedbackInput } from '../models/feedback.model';
import { SubmitContactMessageInput } from '../models/contact-message.model';

// What register and login answer: the User of the contract, plus the access
// token beside it. Only the User goes on to AuthService; the token stays in
// SessionTokenStore and travels in the Authorization header from then on.
interface AuthResponse {
  user: User;
  accessToken: string;
  expiresIn: number; // seconds
}

// The backend's single error shape — see backend/docs/api-contract.md.
interface ApiErrorBody {
  error: { code: string; message: string };
}

// The Error every method rejects with. `message` is Spanish and meant to be
// shown as is (the registro and ingreso forms already do); `code` and
// `status` are there for whoever needs to tell errors apart.
export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

const NETWORK_ERROR_MESSAGE = 'No pudimos conectarnos con el servidor. Probá de nuevo en unos minutos.';
const UNEXPECTED_ERROR_MESSAGE = 'Ocurrió un error inesperado. Probá de nuevo.';

// ApiService against the Flask backend at environment.apiBaseUrl, one route
// per method (route map in backend/CLAUDE.md). The userId some methods take
// is part of the contract but never sent: the backend gets identity from the
// token alone.
@Injectable()
export class HttpApiService implements ApiService {
  private readonly base = environment.apiBaseUrl.replace(/\/+$/, '');

  constructor(
    private readonly http: HttpClient,
    private readonly tokens: SessionTokenStore,
  ) {
    // Deferred: this service is built while AuthService is still being
    // constructed (AuthService -> API_SERVICE -> here), so the token can only
    // be tied to it once that finishes. Browser-only inside followSession.
    Promise.resolve().then(() => this.tokens.followSession());
  }

  register(input: RegisterInput): Observable<User> {
    return this.http.post<AuthResponse>(this.url('/api/auth/register'), input).pipe(
      map((body) => this.startSession(body)),
      catchError(toApiError),
    );
  }

  login(input: LoginInput): Observable<User> {
    return this.http.post<AuthResponse>(this.url('/api/auth/login'), input).pipe(
      map((body) => this.startSession(body)),
      catchError(toApiError),
    );
  }

  updateProfile(_userId: string, input: UpdateProfileInput): Observable<User> {
    return this.http.patch<User>(this.url('/api/users/me'), input).pipe(catchError(toApiError));
  }

  createTestAttempt(_userId: string): Observable<TestAttempt> {
    return this.http.post<TestAttempt>(this.url('/api/attempts'), null).pipe(catchError(toApiError));
  }

  getQuestions(attemptId: string): Observable<Question[]> {
    return this.http
      .get<Question[]>(this.url(`/api/attempts/${encodeURIComponent(attemptId)}/questions`))
      .pipe(catchError(toApiError));
  }

  submitResponse(attemptId: string, response: NewResponseInput): Observable<TestResponse> {
    // Exactly the four fields of NewResponseInput: the backend rejects any other key.
    const body: NewResponseInput = {
      questionId: response.questionId,
      selectedOptionId: response.selectedOptionId,
      freeTextResponse: response.freeTextResponse,
      orderingResponse: response.orderingResponse,
    };
    return this.http
      .post<TestResponse>(this.url(`/api/attempts/${encodeURIComponent(attemptId)}/responses`), body)
      .pipe(catchError(toApiError));
  }

  getResponses(attemptId: string): Observable<TestResponse[]> {
    return this.http
      .get<TestResponse[]>(this.url(`/api/attempts/${encodeURIComponent(attemptId)}/responses`))
      .pipe(catchError(toApiError));
  }

  completeTestAttempt(attemptId: string): Observable<TestAttempt> {
    return this.http
      .post<TestAttempt>(this.url(`/api/attempts/${encodeURIComponent(attemptId)}/complete`), null)
      .pipe(catchError(toApiError));
  }

  getResult(attemptId: string): Observable<Result> {
    return this.http
      .get<Result>(this.url(`/api/attempts/${encodeURIComponent(attemptId)}/result`))
      .pipe(catchError(toApiError));
  }

  // No attempts yet is a 200 with a JSON null body, which HttpClient already
  // delivers as null.
  getLatestAttempt(_userId: string): Observable<TestAttempt | null> {
    return this.http
      .get<TestAttempt | null>(this.url('/api/attempts/latest'))
      .pipe(catchError(toApiError));
  }

  // The backend answers 404 for an attempt that doesn't exist or isn't this
  // user's; the contract's null is produced here (api-contract.md, 07-10).
  getAttempt(attemptId: string): Observable<TestAttempt | null> {
    return this.http.get<TestAttempt>(this.url(`/api/attempts/${encodeURIComponent(attemptId)}`)).pipe(
      catchError((error: unknown) =>
        error instanceof HttpErrorResponse && error.status === 404 ? of(null) : toApiError(error),
      ),
    );
  }

  getAttemptHistory(_userId: string): Observable<TestAttempt[]> {
    return this.http.get<TestAttempt[]>(this.url('/api/attempts')).pipe(catchError(toApiError));
  }

  submitFeedback(input: SubmitFeedbackInput): Observable<void> {
    return this.http.post(this.url('/api/feedback'), input).pipe(
      map(() => undefined),
      catchError(toApiError),
    );
  }

  submitContactMessage(input: SubmitContactMessageInput): Observable<void> {
    return this.http.post(this.url('/api/contact-messages'), input).pipe(
      map(() => undefined),
      catchError(toApiError),
    );
  }

  private url(path: string): string {
    return `${this.base}${path}`;
  }

  // The token is stored before the User is handed back, so by the time
  // AuthService sets the user, the session it represents is complete.
  private startSession(body: AuthResponse): User {
    this.tokens.save(body.accessToken, body.expiresIn);
    return body.user;
  }
}

function toApiError(error: unknown): Observable<never> {
  return throwError(() => asApiError(error));
}

function asApiError(error: unknown): ApiError {
  if (!(error instanceof HttpErrorResponse)) {
    return new ApiError(UNEXPECTED_ERROR_MESSAGE, 'UNEXPECTED_ERROR', 0);
  }
  if (error.status === 0) {
    return new ApiError(NETWORK_ERROR_MESSAGE, 'NETWORK_ERROR', 0);
  }
  const body = error.error as Partial<ApiErrorBody> | null;
  const apiError = body && typeof body === 'object' ? body.error : undefined;
  if (apiError && typeof apiError.message === 'string' && typeof apiError.code === 'string') {
    return new ApiError(apiError.message, apiError.code, error.status);
  }
  return new ApiError(UNEXPECTED_ERROR_MESSAGE, 'HTTP_ERROR', error.status);
}
