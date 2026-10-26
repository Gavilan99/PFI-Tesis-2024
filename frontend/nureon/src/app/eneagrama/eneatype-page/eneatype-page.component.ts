import { Component, DestroyRef, ElementRef, Inject, OnInit, PLATFORM_ID, ViewChild } from '@angular/core';
import { AsyncPipe, ViewportScroller, isPlatformBrowser } from '@angular/common';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { Observable } from 'rxjs';
import { User } from '../../core/models/user.model';
import { AuthService } from '../../core/services/auth.service';
import { PageContainerComponent } from '../../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../../shared/components/brand-button/brand-button.component';
import { ENEATYPE_STRUCTURE } from '../../resultados/enneagram-diagram/enneagram-diagram.component';
import { ENEATYPE_CONTENT, EneatypeContent, TRIADS, eneatypeLabel } from '../../resultados/eneatype-content';
import { parseEneatype } from '../eneatype-route';

// /eneagrama/:tipo — the short, public page per type: strengths,
// weaknesses, growth and tensions, from ENEATYPE_CONTENT[n].page and never
// from the result's text. Growth and tensions name the type each one moves
// toward, read from ENEATYPE_STRUCTURE, the same lines the result's diagram
// draws, so the two can't disagree. Prerendered, no ApiService call; the
// closing CTA follows the session like the landing's hero does.
//
// The router reuses this component from /eneagrama/1 to /eneagrama/2, so the
// type comes from paramMap on every change, not from a snapshot.
//
// Every link here is an app-brand-button, and RouterLink stays out of
// `imports` on purpose: imported, it also matches the routerLink input on
// the <app-brand-button> host, which then navigates a second time on each
// click (previous/next skipped a type) and adds an empty Tab stop.
@Component({
  selector: 'app-eneatype-page',
  standalone: true,
  imports: [AsyncPipe, PageContainerComponent, BrandButtonComponent],
  templateUrl: './eneatype-page.component.html',
  styleUrl: './eneatype-page.component.scss',
})
export class EneatypePageComponent implements OnInit {
  @ViewChild('heading') private heading?: ElementRef<HTMLElement>;

  readonly user$: Observable<User | null>;
  eneatype = 1;
  private readonly isBrowser: boolean;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly viewportScroller: ViewportScroller,
    private readonly destroyRef: DestroyRef,
    auth: AuthService,
    @Inject(PLATFORM_ID) platformId: object,
  ) {
    this.user$ = auth.currentUserChanges;
    this.isBrowser = isPlatformBrowser(platformId);
  }

  ngOnInit(): void {
    this.route.paramMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((params) => {
      // eneatypeGuard already turned away anything that isn't 1-9.
      this.eneatype = parseEneatype(params.get('tipo')) ?? 1;
      this.onTypeShown();
    });
  }

  get content(): EneatypeContent {
    return ENEATYPE_CONTENT[this.eneatype];
  }

  get label(): string {
    return eneatypeLabel(this.eneatype);
  }

  get triadName(): string {
    return TRIADS.find((triad) => triad.id === this.content.triad)!.name;
  }

  get colorVar(): string {
    return `var(${this.content.color})`;
  }

  get growthTo(): number {
    return ENEATYPE_STRUCTURE[this.eneatype].integratesTo;
  }

  get stressTo(): number {
    return ENEATYPE_STRUCTURE[this.eneatype].disintegratesTo;
  }

  // 9 → 1 and 1 → 9: the nine types are a circle, like the diagram.
  get previous(): number {
    return this.eneatype === 1 ? 9 : this.eneatype - 1;
  }

  get next(): number {
    return this.eneatype === 9 ? 1 : this.eneatype + 1;
  }

  labelOf(eneatype: number): string {
    return eneatypeLabel(eneatype);
  }

  // The app doesn't restore scroll on navigation, and every link into this
  // page (the cards, previous/next) sits halfway down or at the bottom: start
  // each type at the top. When the visitor got here from inside the app, the
  // link they used is gone or now says something else, so focus moves to the
  // new heading for keyboard and screen reader users. Not on a fresh load:
  // there the browser's own starting point is the right one.
  private onTypeShown(): void {
    if (!this.isBrowser) {
      return;
    }
    this.viewportScroller.scrollToPosition([0, 0]);
    if (this.router.navigated) {
      setTimeout(() => this.heading?.nativeElement.focus({ preventScroll: true }));
    }
  }
}
