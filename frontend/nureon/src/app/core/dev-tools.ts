import { Injector, NgZone } from '@angular/core';
import { Router } from '@angular/router';
import { take } from 'rxjs';
import { AuthService } from './services/auth.service';
import { API_SERVICE, ApiService } from './services/api.service';
import { UserJourneyStateService } from './services/user-journey-state.service';

interface NureonDevTools {
  login: () => void;
  logout: () => void;
  startAttempt: () => void;
  completeLatestAttempt: () => void;
  goto: (path: string) => void;
  debugState: () => void;
  breakResultLoading: () => void;
}

const MOCK_STATE_STORAGE_KEY = 'nureon_mock_api_state';

// Console helpers to exercise the four user-journey states without the real
// login/test flow (Stages 4/5) built yet. Only called from AppComponent when
// !environment.production and isPlatformBrowser — never touches `window`
// during SSR/prerender, and never ships in the production bundle's reachable
// code path.
//
// The mock auth/attempt state lives only in memory (no localStorage, no
// server session) — typing a URL in the address bar triggers a full page
// reload, which re-bootstraps the app and resets it. Use goto() to navigate
// client-side instead, so state set via login()/startAttempt() actually
// carries over to the next route's guard check.
//
// Every entry point runs inside NgZone.run(): these are invoked from the
// browser console, outside Angular's zone, so without it neither the
// BehaviorSubject-driven guards nor the router's own change detection would
// pick up the change.
export function installDevTools(injector: Injector): void {
  const auth = injector.get(AuthService);
  const api = injector.get<ApiService>(API_SERVICE);
  const router = injector.get(Router);
  const zone = injector.get(NgZone);
  const journeyState = injector.get(UserJourneyStateService);

  const tools: NureonDevTools = {
    login: () => zone.run(() => auth.setAuthenticated(true)),
    logout: () => zone.run(() => auth.setAuthenticated(false)),
    startAttempt: () => {
      zone.run(() => {
        api.createTestAttempt().subscribe((attempt) => console.log('Attempt started:', attempt));
      });
    },
    completeLatestAttempt: () => {
      zone.run(() => {
        api.getLatestAttempt().subscribe((attempt) => {
          if (!attempt) {
            console.warn('No attempt to complete — call nureonDev.startAttempt() first.');
            return;
          }
          api
            .completeTestAttempt(attempt.id)
            .subscribe((a) => console.log('Attempt completed:', a));
        });
      });
    },
    goto: (path: string) => {
      zone.run(() => {
        router.navigateByUrl(path).then(() => {
          // navigateByUrl resolves false whenever a guard redirects to a
          // different URL — that's the expected, successful outcome for a
          // blocked route, not a failure. Log where it actually landed
          // instead of treating that as an error.
          console.log(`goto("${path}") landed on:`, router.url);
        });
      });
    },
    debugState: () => {
      console.log('auth.isAuthenticated (raw):', auth.isAuthenticated);
      journeyState.state$.pipe(take(1)).subscribe({
        next: (state) => console.log('journey state:', state),
        error: (err) => console.error('journey state errored:', err),
      });
    },
    // Simulates CU004's alternate flow (error loading the result) — deletes
    // the persisted result for the latest attempt directly from
    // localStorage, so MockApiService.getResult() throws next time
    // /resultados asks for it. There's no ApiService method for this on
    // purpose: a real backend wouldn't expose "corrupt my own data" either.
    breakResultLoading: () => {
      try {
        const raw = localStorage.getItem(MOCK_STATE_STORAGE_KEY);
        if (!raw) {
          console.warn('No hay estado de MockApiService en localStorage todavía.');
          return;
        }
        const state = JSON.parse(raw);
        const attemptId = state.latestAttemptId;
        if (!attemptId || !state.resultsByAttempt?.[attemptId]) {
          console.warn('No hay un resultado para el último intento — completá el test primero.');
          return;
        }
        delete state.resultsByAttempt[attemptId];
        localStorage.setItem(MOCK_STATE_STORAGE_KEY, JSON.stringify(state));
        console.log(
          `Resultado borrado para el intento "${attemptId}". Recargá /resultados para ver el estado de error.`,
        );
      } catch (err) {
        console.error('No se pudo romper el resultado:', err);
      }
    },
  };

  (window as unknown as { nureonDev: NureonDevTools }).nureonDev = tools;
  console.info(
    'nureonDev tools available: login(), logout(), startAttempt(), completeLatestAttempt(), ' +
      'goto(path), breakResultLoading() — use goto() to navigate without a full page reload, ' +
      'or state resets.',
  );
}
