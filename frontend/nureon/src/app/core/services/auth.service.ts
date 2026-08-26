import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

// Mock session state — Cognito integration is Stage 4 scope. Exists now so
// the user-journey state machine and its guards have something real to read
// against, without building a fake login flow ahead of schedule. Toggled
// via the dev console helpers in core/dev-tools.ts until real login exists.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly authenticated$ = new BehaviorSubject<boolean>(false);
  readonly isAuthenticated$ = this.authenticated$.asObservable();

  get isAuthenticated(): boolean {
    return this.authenticated$.value;
  }

  setAuthenticated(value: boolean): void {
    this.authenticated$.next(value);
  }
}
