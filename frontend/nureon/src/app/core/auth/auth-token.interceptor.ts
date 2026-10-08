import { Injectable } from '@angular/core';
import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest,
} from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SessionTokenStore } from './session-token.store';

// Sends the stored access token to the backend, and only to the backend: a
// request to any other origin (or to a static asset) goes out untouched.
// A 401 from the backend ends the session — except from /api/auth/*, where a
// 401 means "wrong email or password" on a login form with no session yet.
@Injectable()
export class AuthTokenInterceptor implements HttpInterceptor {
  constructor(private readonly tokens: SessionTokenStore) {}

  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    if (!isApiUrl(req.url)) {
      return next.handle(req);
    }
    // AuthService necessarily exists by the time a request is made, so this
    // is the earliest safe point to tie the token to it (see followSession).
    this.tokens.followSession();
    const token = this.tokens.accessToken();
    const authorized = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
    return next.handle(authorized).pipe(
      catchError((error: unknown) => {
        if (
          error instanceof HttpErrorResponse &&
          error.status === 401 &&
          !req.url.startsWith(`${apiBase()}/api/auth/`)
        ) {
          this.tokens.invalidateSession();
        }
        return throwError(() => error);
      }),
    );
  }
}

function apiBase(): string {
  return environment.apiBaseUrl.replace(/\/+$/, '');
}

function isApiUrl(url: string): boolean {
  const base = apiBase();
  return base !== '' && url.startsWith(`${base}/`);
}
