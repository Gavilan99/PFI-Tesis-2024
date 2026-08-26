import { Component } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

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
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
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
}
