import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import {
  LEGAL_CONTACT_EMAIL,
  LEGAL_RESPONSIBLE,
  LEGAL_TEXT_DATE,
  LEGAL_TEXT_VERSION,
} from '../legal/legal-content';

// Public, prerendered. What Ley 25.326 art. 6 asks to inform before
// collecting, plus the transfer to the United States (art. 12, decreto
// 1558/2001). The responsible party and the contact address come from
// legal-content.ts, still as markers until they're decided.
@Component({
  selector: 'app-privacidad',
  standalone: true,
  imports: [PageContainerComponent, RouterLink],
  templateUrl: './privacidad.component.html',
  styleUrl: '../legal/legal-page.scss',
})
export class PrivacidadComponent {
  readonly responsible = LEGAL_RESPONSIBLE;
  readonly contactEmail = LEGAL_CONTACT_EMAIL;
  readonly version = LEGAL_TEXT_VERSION;
  readonly versionDate = LEGAL_TEXT_DATE;
}
