import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CutStatus } from '../../core/models/cut-status.model';
import { CUT_COPY } from '../../core/cuts/cut-copy';
import { BrandButtonComponent } from '../../shared/components/brand-button/brand-button.component';
import { PremiumButtonComponent } from '../../shared/components/premium-button/premium-button.component';

// Feature 10 — the "afinar tu resultado" block of /resultados: answer the
// next cut without repeating what's already answered. Only shows and emits:
// ResultadosComponent decides whether it appears and does the continuing.
@Component({
  selector: 'app-refine-result',
  standalone: true,
  imports: [BrandButtonComponent, PremiumButtonComponent],
  templateUrl: './refine-result.component.html',
  styleUrl: './refine-result.component.scss',
})
export class RefineResultComponent {
  @Input({ required: true }) status!: CutStatus;
  // True with the paid tier: "Seguir". Otherwise, the plans text.
  @Input() canContinue = false;
  @Input() busy = false;
  @Input() error: string | null = null;
  // Where "Pasar a premium" comes back to: this result, where "Seguir" then
  // continues in a new attempt linked to it (RF16).
  @Input() returnTo = '/resultados';
  @Output() continue = new EventEmitter<void>();

  readonly copy = CUT_COPY;
}
