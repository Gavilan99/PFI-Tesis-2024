import { Injectable } from '@angular/core';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, NavigationEnd, Router } from '@angular/router';
import { filter, map, mergeMap } from 'rxjs';

const BRAND_SUFFIX = 'NureonAI';

// Keeps document.title in sync with the active route's data.title — the
// same value PlaceholderComponent renders as its on-page heading, so there's
// one source for both. Works identically during SSR/prerender: Angular's
// Title service mutates the server-rendered document, which then gets
// serialized into the prerendered HTML, giving every route its own <title>.
@Injectable({ providedIn: 'root' })
export class PageTitleService {
  constructor(
    private readonly title: Title,
    private readonly router: Router,
    private readonly activatedRoute: ActivatedRoute,
  ) {}

  init(): void {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        map(() => {
          let route = this.activatedRoute;
          while (route.firstChild) {
            route = route.firstChild;
          }
          return route;
        }),
        mergeMap((route) => route.data),
      )
      .subscribe((data) => {
        const routeTitle = data['title'] as string | undefined;
        this.title.setTitle(routeTitle ? `${routeTitle} · ${BRAND_SUFFIX}` : BRAND_SUFFIX);
      });
  }
}
