import { Component } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { HeaderComponent } from '../shared/layout/header/header.component';
import { FooterComponent } from '../shared/layout/footer/footer.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { CardComponent } from '../shared/components/card/card.component';
import { EnneatypeBadgeComponent } from '../shared/components/enneatype-badge/enneatype-badge.component';
import { ProgressBarComponent } from '../shared/components/progress-bar/progress-bar.component';
import { EmptyStateComponent } from '../shared/components/empty-state/empty-state.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';

const PALETTE_TINTS = [
  '50', '100', '200', '300', '400', '500', '600', '700', '800', '900',
  'A100', 'A200', 'A400', 'A700',
];

@Component({
  selector: 'app-styleguide',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    PageContainerComponent,
    HeaderComponent,
    FooterComponent,
    BrandButtonComponent,
    CardComponent,
    EnneatypeBadgeComponent,
    ProgressBarComponent,
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingStateComponent,
  ],
  templateUrl: './styleguide.component.html',
  styleUrl: './styleguide.component.scss',
})
export class StyleguideComponent {
  readonly paletteTints = PALETTE_TINTS;

  // Pre-filled and marked invalid on load, purely to demo the error state
  // without requiring the reviewer to interact with the field first.
  readonly emailWithError = new FormControl('no-es-un-email', [
    Validators.required,
    Validators.email,
  ]);

  constructor() {
    this.emailWithError.markAsTouched();
  }

  onRetry(): void {
    console.log('Retry clicked in styleguide demo — no-op.');
  }
}
