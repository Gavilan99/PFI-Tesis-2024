import { Inject, Injectable } from '@angular/core';
import { Observable, map, of, switchMap } from 'rxjs';
import { AuthService } from './auth.service';
import { API_SERVICE, ApiService } from './api.service';
import { UserJourneyState } from '../models/user-journey-state.model';

// Explicit user-journey state machine: no-account -> account-no-attempts ->
// attempt-in-progress -> attempt-completed. Routes and guards read state$
// instead of checking auth/attempts separately, so "which state is this
// route valid in" stays a single, explicit question.
@Injectable({ providedIn: 'root' })
export class UserJourneyStateService {
  constructor(
    private readonly auth: AuthService,
    @Inject(API_SERVICE) private readonly api: ApiService,
  ) {}

  readonly state$: Observable<UserJourneyState> = this.auth.isAuthenticated$.pipe(
    switchMap((isAuthenticated) => {
      if (!isAuthenticated) {
        return of<UserJourneyState>('no-account');
      }
      return this.api.getLatestAttempt().pipe(
        map((attempt): UserJourneyState => {
          if (!attempt) {
            return 'account-no-attempts';
          }
          // 'abandoned' is treated the same as 'in_progress' for now — richer
          // handling (offer to resume vs. start over) is Stage 5 territory.
          return attempt.status === 'completed' ? 'attempt-completed' : 'attempt-in-progress';
        }),
      );
    }),
  );
}
