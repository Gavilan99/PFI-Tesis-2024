import { Injector } from '@angular/core';
import { AuthService } from './services/auth.service';
import { API_SERVICE, ApiService } from './services/api.service';

interface NureonDevTools {
  login: () => void;
  logout: () => void;
  startAttempt: () => void;
  completeLatestAttempt: () => void;
}

// Console helpers to exercise the four user-journey states without the real
// login/test flow (Stages 4/5) built yet. Only called from AppComponent when
// !environment.production and isPlatformBrowser — never touches `window`
// during SSR/prerender, and never ships in the production bundle's reachable
// code path.
export function installDevTools(injector: Injector): void {
  const auth = injector.get(AuthService);
  const api = injector.get<ApiService>(API_SERVICE);

  const tools: NureonDevTools = {
    login: () => auth.setAuthenticated(true),
    logout: () => auth.setAuthenticated(false),
    startAttempt: () => {
      api.createTestAttempt().subscribe((attempt) => console.log('Attempt started:', attempt));
    },
    completeLatestAttempt: () => {
      api.getLatestAttempt().subscribe((attempt) => {
        if (!attempt) {
          console.warn('No attempt to complete — call nureonDev.startAttempt() first.');
          return;
        }
        api.completeTestAttempt(attempt.id).subscribe((a) => console.log('Attempt completed:', a));
      });
    },
  };

  (window as unknown as { nureonDev: NureonDevTools }).nureonDev = tools;
  console.info(
    'nureonDev tools available: login(), logout(), startAttempt(), completeLatestAttempt()',
  );
}
