import { Component, Inject, Injector, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { NavigationEnd, Router } from '@angular/router';
import { filter, map, pairwise, startWith } from 'rxjs';
import { environment } from '../environments/environment';
import { installDevTools } from './core/dev-tools';
import { AuthService } from './core/services/auth.service';
import { PageTitleService } from './core/services/page-title.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'nureon';
  readonly isAuthenticated$ = this.auth.isAuthenticated$;

  // Hidden on /test: a 40-item questionnaire doesn't need "Política de
  // privacidad · Términos y condiciones" competing with the question for
  // attention on every screen (Stage 10). Route-based, not a per-component
  // flag, since the footer lives in the shell, outside the router-outlet.
  readonly showFooter$ = this.router.events.pipe(
    filter((event): event is NavigationEnd => event instanceof NavigationEnd),
    map((event) => !event.urlAfterRedirects.startsWith('/test')),
    startWith(!this.router.url.startsWith('/test')),
  );

  constructor(
    injector: Injector,
    @Inject(PLATFORM_ID) platformId: object,
    private readonly auth: AuthService,
    private readonly router: Router,
    pageTitle: PageTitleService,
  ) {
    pageTitle.init();
    if (!environment.production && isPlatformBrowser(platformId)) {
      installDevTools(injector);
    }

    // When the session ends (the header's "Cerrar sesión", or a 401 from the
    // backend) the screen on view is re-checked against its guards, so a
    // protected screen (/perfil, /resultados, /test, /inicio) is left for
    // /ingresar instead of keeping the previous account's data on view.
    // Public screens have no guards and stay where they are. Needs
    // runGuardsAndResolvers: 'always' on the protected routes, or a reload of
    // the same URL would skip the guards.
    this.auth.currentUserChanges
      .pipe(
        pairwise(),
        filter(([previous, current]) => previous !== null && current === null),
      )
      .subscribe(() => {
        this.router.navigateByUrl(this.router.url, { onSameUrlNavigation: 'reload' });
      });
  }

  onLogoutRequested(): void {
    this.auth.logout();
  }
}
