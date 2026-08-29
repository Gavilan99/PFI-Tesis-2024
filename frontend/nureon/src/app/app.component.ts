import { Component, Inject, Injector, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
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

  constructor(
    injector: Injector,
    @Inject(PLATFORM_ID) platformId: object,
    private readonly auth: AuthService,
    pageTitle: PageTitleService,
  ) {
    pageTitle.init();
    if (!environment.production && isPlatformBrowser(platformId)) {
      installDevTools(injector);
    }
  }

  onLogoutRequested(): void {
    this.auth.setAuthenticated(false);
  }
}
