import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { CardComponent } from '../shared/components/card/card.component';

// Public, prerendered entry point. No client-only APIs, no ApiService call —
// pure marketing content, same as every route in this stage. The one
// exception is the notice after deleting an account (Feature 11): /perfil
// navigates here with { accountDeleted: true } in the navigation state. Only
// a client-side navigation carries it, so the prerendered page never shows it.
@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [PageContainerComponent, BrandButtonComponent, CardComponent],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class LandingComponent {
  readonly accountDeleted: boolean;

  constructor(router: Router) {
    this.accountDeleted = router.getCurrentNavigation()?.extras.state?.['accountDeleted'] === true;
  }
}
