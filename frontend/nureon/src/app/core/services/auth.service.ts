import { Inject, Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { API_SERVICE, ApiService } from './api.service';
import { LoginInput, RegisterInput } from '../models/auth.model';
import { User } from '../models/user.model';

// Mock session state, plus the register()/login() orchestration (call
// ApiService, then flip the flag on success) so RegistroComponent/
// IngresoComponent don't each have to remember to do both steps. Real
// Cognito integration replaces the ApiService call underneath this, not
// this class's shape — see RNF09's "ranura" in the redesign plan. Also
// toggled directly via the dev console helpers in core/dev-tools.ts.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly authenticated$ = new BehaviorSubject<boolean>(false);
  readonly isAuthenticated$ = this.authenticated$.asObservable();

  constructor(@Inject(API_SERVICE) private readonly api: ApiService) {}

  get isAuthenticated(): boolean {
    return this.authenticated$.value;
  }

  setAuthenticated(value: boolean): void {
    this.authenticated$.next(value);
  }

  register(input: RegisterInput): Observable<User> {
    return this.api.register(input).pipe(tap(() => this.setAuthenticated(true)));
  }

  login(input: LoginInput): Observable<User> {
    return this.api.login(input).pipe(tap(() => this.setAuthenticated(true)));
  }
}
