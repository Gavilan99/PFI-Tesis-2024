import { Component } from '@angular/core';
import { AsyncPipe } from '@angular/common';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { User } from '../core/models/user.model';
import { AuthService } from '../core/services/auth.service';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { CardComponent } from '../shared/components/card/card.component';

// Public, prerendered entry point. No client-only APIs, no ApiService call —
// pure marketing content, same as every route in this stage. The one
// exception is the notice after deleting an account (Feature 11): /perfil
// navigates here with { accountDeleted: true } in the navigation state. Only
// a client-side navigation carries it, so the prerendered page never shows it.
// With a session the hero greets the person and points to /perfil instead of
// /registro; the prerendered page has no session, so it's the logged-out one.
@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [AsyncPipe, PageContainerComponent, BrandButtonComponent, CardComponent],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class LandingComponent {
  readonly accountDeleted: boolean;
  readonly user$: Observable<User | null>;

  constructor(router: Router, auth: AuthService) {
    this.user$ = auth.currentUserChanges;
    this.accountDeleted = router.getCurrentNavigation()?.extras.state?.['accountDeleted'] === true;
  }
}
