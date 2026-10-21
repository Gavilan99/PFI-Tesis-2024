import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { LEGAL_CONTACT_EMAIL, LEGAL_TEXT_DATE, LEGAL_TEXT_VERSION } from '../legal/legal-content';

// Public, prerendered. Use of the service, the result as guidance (not a
// clinical diagnosis), and the free and premium plans.
@Component({
  selector: 'app-terminos',
  standalone: true,
  imports: [PageContainerComponent, RouterLink],
  templateUrl: './terminos.component.html',
  styleUrl: '../legal/legal-page.scss',
})
export class TerminosComponent {
  readonly contactEmail = LEGAL_CONTACT_EMAIL;
  readonly version = LEGAL_TEXT_VERSION;
  readonly versionDate = LEGAL_TEXT_DATE;
}
