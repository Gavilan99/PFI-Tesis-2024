import { Component } from '@angular/core';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { CardComponent } from '../shared/components/card/card.component';

// Public, prerendered entry point. No client-only APIs, no ApiService call —
// pure marketing content, same as every route in this stage.
@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [PageContainerComponent, BrandButtonComponent, CardComponent],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.scss',
})
export class LandingComponent {}
