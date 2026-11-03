import { Component, Input } from '@angular/core';

// Feature 20/21 — "Evaluación de: <identificador>", shown on the test, the screen between cuts
// and the result whenever the attempt was administered to an evaluado rather than taken by the
// account itself. Renders nothing without a label, so every caller can bind it unconditionally.
@Component({
  selector: 'app-subject-banner',
  standalone: true,
  templateUrl: './subject-banner.component.html',
  styleUrl: './subject-banner.component.scss',
})
export class SubjectBannerComponent {
  @Input() label: string | null = null;
}
