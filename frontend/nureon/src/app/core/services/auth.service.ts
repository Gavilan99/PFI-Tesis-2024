import { Inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BehaviorSubject, Observable, map, tap } from 'rxjs';
import { API_SERVICE, ApiService } from './api.service';
import { LoginInput, RegisterInput } from '../models/auth.model';
import { User, UpdateProfileInput } from '../models/user.model';

const STORAGE_KEY = 'nureon_mock_auth_user';

// Mock session state, plus the register()/login()/updateProfile()
// orchestration (call ApiService, then update the held user on success) so
// components don't each have to remember to do both steps. Real Cognito
// integration replaces the ApiService calls underneath this, not this
// class's shape — see RNF09's "ranura" in the redesign plan.
//
// Holds the current User, not just a boolean: Stage 7's profile screen
// needs to know *who*, not just *whether*. Persisted to localStorage: a real
// session survives a page reload via Cognito's own token storage, and the
// mock needs to approximate that or reloading mid-test (Stage 5) would
// bounce the user out through sessionGuard before the resumed attempt is
// ever reached.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly isBrowser: boolean;
  private readonly currentUser$: BehaviorSubject<User | null>;
  readonly isAuthenticated$: Observable<boolean>;

  constructor(
    @Inject(API_SERVICE) private readonly api: ApiService,
    @Inject(PLATFORM_ID) platformId: object,
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
    this.currentUser$ = new BehaviorSubject<User | null>(this.readPersisted());
    this.isAuthenticated$ = this.currentUser$.pipe(map((user) => user !== null));
  }

  get isAuthenticated(): boolean {
    return this.currentUser$.value !== null;
  }

  get currentUser(): User | null {
    return this.currentUser$.value;
  }

  get currentUserChanges(): Observable<User | null> {
    return this.currentUser$.asObservable();
  }

  setUser(user: User | null): void {
    this.currentUser$.next(user);
    this.persist(user);
  }

  register(input: RegisterInput): Observable<User> {
    return this.api.register(input).pipe(tap((user) => this.setUser(user)));
  }

  login(input: LoginInput): Observable<User> {
    return this.api.login(input).pipe(tap((user) => this.setUser(user)));
  }

  logout(): void {
    this.setUser(null);
  }

  updateProfile(input: UpdateProfileInput): Observable<User> {
    const user = this.currentUser;
    if (!user) {
      throw new Error('AuthService.updateProfile() called with no user logged in.');
    }
    return this.api.updateProfile(user.id, input).pipe(tap((updated) => this.setUser(updated)));
  }

  private readPersisted(): User | null {
    if (!this.isBrowser) {
      return null;
    }
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  }

  private persist(user: User | null): void {
    if (!this.isBrowser) {
      return;
    }
    try {
      if (user) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Storage unavailable — session just won't survive a reload this time.
    }
  }
}
