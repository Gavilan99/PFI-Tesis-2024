import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { API_SERVICE, ApiService } from './api.service';
import { LoginInput, RegisterInput } from '../models/auth.model';
import { User } from '../models/user.model';

const STORAGE_KEY = 'nureon_mock_auth';

// Mock session state, plus the register()/login() orchestration (call
// ApiService, then flip the flag on success) so RegistroComponent/
// IngresoComponent don't each have to remember to do both steps. Real
// Cognito integration replaces the ApiService call underneath this, not
// this class's shape — see RNF09's "ranura" in the redesign plan. Also
// toggled directly via the dev console helpers in core/dev-tools.ts.
//
// Persisted to localStorage: a real session survives a page reload via
// Cognito's own token storage, and the mock needs to approximate that or
// reloading mid-test (Stage 5) would bounce the user out through
// sessionGuard before the resumed attempt is ever reached.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly isBrowser: boolean;
  private readonly authenticated$: BehaviorSubject<boolean>;
  readonly isAuthenticated$: Observable<boolean>;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    @Inject(PLATFORM_ID) platformId: object,
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
    this.authenticated$ = new BehaviorSubject<boolean>(this.readPersisted());
    this.isAuthenticated$ = this.authenticated$.asObservable();
  }

  get isAuthenticated(): boolean {
    return this.authenticated$.value;
  }

  setAuthenticated(value: boolean): void {
    this.authenticated$.next(value);
    this.persist(value);
  }

  register(input: RegisterInput): Observable<User> {
    return this.api.register(input).pipe(tap(() => this.setAuthenticated(true)));
  }

  login(input: LoginInput): Observable<User> {
    return this.api.login(input).pipe(tap(() => this.setAuthenticated(true)));
  }

  private readPersisted(): boolean {
    if (!this.isBrowser) {
      return false;
    }
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  }

  private persist(value: boolean): void {
    if (!this.isBrowser) {
      return;
    }
    try {
      localStorage.setItem(STORAGE_KEY, String(value));
    } catch {
      // Storage unavailable — session just won't survive a reload this time.
    }
  }
}
