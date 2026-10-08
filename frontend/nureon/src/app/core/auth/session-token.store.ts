import { Inject, Injectable, Injector, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { AuthService } from '../services/auth.service';

const STORAGE_KEY = 'nureon_access_token';

// A token this close to expiring is treated as already expired: a request
// sent with it could reach the backend after it lapses.
const EXPIRY_MARGIN_MS = 30_000;

interface StoredToken {
  accessToken: string;
  expiresAt: number; // epoch ms
}

// The backend's access token, kept in localStorage next to the user that
// AuthService persists there, so reloading mid-test resumes with a valid
// session. Never touched during SSR/prerender: there is no localStorage on
// the server, and a server-side render never carries a session anyway.
//
// The token follows AuthService's user without AuthService knowing about it:
// when the user goes to null (logout), the token is dropped; when a user is
// held but there is no valid token (expired, or a session left over from the
// mock), the user is logged out, so the app never sits in a "logged in, every
// request 401s" state.
@Injectable({ providedIn: 'root' })
export class SessionTokenStore {
  private readonly isBrowser: boolean;
  private following = false;

  constructor(
    @Inject(PLATFORM_ID) platformId: object,
    private readonly injector: Injector,
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
  }

  save(accessToken: string, expiresInSeconds: number): void {
    if (!this.isBrowser) {
      return;
    }
    const stored: StoredToken = { accessToken, expiresAt: Date.now() + expiresInSeconds * 1000 };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    } catch {
      // Storage unavailable — the token just won't survive a reload.
    }
  }

  // The stored access token, or null if there is none or it has expired.
  // An expired one is dropped on the way.
  accessToken(): string | null {
    if (!this.isBrowser) {
      return null;
    }
    let stored: StoredToken | null = null;
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      stored = raw ? (JSON.parse(raw) as StoredToken) : null;
    } catch {
      stored = null;
    }
    if (!stored || typeof stored.accessToken !== 'string' || typeof stored.expiresAt !== 'number') {
      return null;
    }
    if (stored.expiresAt - EXPIRY_MARGIN_MS <= Date.now()) {
      this.clear();
      return null;
    }
    return stored.accessToken;
  }

  clear(): void {
    if (!this.isBrowser) {
      return;
    }
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Nothing to remove from storage that isn't there.
    }
  }

  // Ties the token to AuthService's user, once. Idempotent. AuthService is
  // resolved here, at call time, never in the constructor: AuthService ->
  // API_SERVICE -> HttpApiService -> this store is a construction chain, and
  // asking for AuthService inside it is a DI cycle. Callers invoke this only
  // once AuthService exists (after construction, or from a request).
  followSession(): void {
    if (!this.isBrowser || this.following) {
      return;
    }
    this.following = true;
    const auth = this.injector.get(AuthService);
    auth.currentUserChanges.subscribe((user) => {
      if (user === null) {
        this.clear();
      } else if (this.accessToken() === null) {
        auth.logout();
      }
    });
  }

  // Called on a 401 from the backend: the token is no good anymore, and
  // neither is the session built on it.
  invalidateSession(): void {
    this.clear();
    if (this.isBrowser) {
      this.injector.get(AuthService).logout();
    }
  }
}
