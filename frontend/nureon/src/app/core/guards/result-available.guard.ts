import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, take } from 'rxjs';
import { UserJourneyStateService } from '../services/user-journey-state.service';

// Requires a completed attempt: blocks /resultados and /resultados/:attemptId
// unless the journey state is 'attempt-completed'. No account -> /ingresar;
// account but nothing completed yet -> /inicio, not a dead end.
export const resultAvailableGuard: CanActivateFn = () => {
  const journeyState = inject(UserJourneyStateService);
  const router = inject(Router);

  return journeyState.state$.pipe(
    take(1),
    map((state) => {
      if (state === 'no-account') {
        return router.parseUrl('/ingresar');
      }
      if (state !== 'attempt-completed') {
        return router.parseUrl('/inicio');
      }
      return true;
    }),
  );
};
