import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, take } from 'rxjs';
import { UserJourneyStateService } from '../services/user-journey-state.service';

// Requires an account: blocks 'no-account' from routes like /inicio, /test,
// /perfil. Redirects to /ingresar instead of silently letting the route load.
export const sessionGuard: CanActivateFn = () => {
  const journeyState = inject(UserJourneyStateService);
  const router = inject(Router);

  return journeyState.state$.pipe(
    take(1),
    map((state) => (state === 'no-account' ? router.parseUrl('/ingresar') : true)),
  );
};
