import { Component, Inject, Injector, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { NavigationEnd, Router } from '@angular/router';
import { filter, map, startWith } from 'rxjs';
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
  }

  onLogoutRequested(): void {
    this.auth.logout();
  }
}
