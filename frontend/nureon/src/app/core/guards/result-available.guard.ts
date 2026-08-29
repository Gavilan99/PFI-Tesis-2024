import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, of, switchMap, take } from 'rxjs';
import { UserJourneyStateService } from '../services/user-journey-state.service';
import { AuthService } from '../services/auth.service';
import { API_SERVICE, ApiService } from '../services/api.service';

// Requires a completed attempt: blocks /resultados and /resultados/:attemptId
// unless there's one to show. No account -> /ingresar; account but nothing
// completed anywhere -> /inicio, not a dead end.
//
// Doesn't shortcut on 'attempt-completed' alone: that state reflects only the
// *latest* attempt (UserJourneyStateService), but Stage 7's history lets you
// open /resultados/:attemptId for an OLDER completed attempt even while the
// newest one is still in progress or abandoned — journey state alone would
// wrongly block that.
export const resultAvailableGuard: CanActivateFn = () => {
  const journeyState = inject(UserJourneyStateService);
  const auth = inject(AuthService);
  const api = inject<ApiService>(API_SERVICE);
  const router = inject(Router);

  return journeyState.state$.pipe(
    take(1),
    switchMap((state) => {
      if (state === 'no-account') {
        return of(router.parseUrl('/ingresar'));
      }
      if (state === 'attempt-completed') {
        return of(true);
      }
      const userId = auth.currentUser?.id;
      if (!userId) {
        return of(router.parseUrl('/ingresar'));
      }
      return api
        .getAttemptHistory(userId)
        .pipe(
          map((attempts) =>
            attempts.some((a) => a.status === 'completed') ? true : router.parseUrl('/inicio'),
          ),
        );
    }),
  );
};
