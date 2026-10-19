import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CutStatus } from '../../core/models/cut-status.model';
import { CUT_COPY } from '../../core/cuts/cut-copy';
import { BrandButtonComponent } from '../../shared/components/brand-button/brand-button.component';

// Feature 10 — the "afinar tu resultado" block of /resultados: answer the
// next cut without repeating what's already answered. Only shows and emits:
// ResultadosComponent decides whether it appears and does the continuing.
@Component({
  selector: 'app-refine-result',
  standalone: true,
  imports: [BrandButtonComponent],
  templateUrl: './refine-result.component.html',
  styleUrl: './refine-result.component.scss',
})
export class RefineResultComponent {
  @Input({ required: true }) status!: CutStatus;
  // True with the paid tier: "Seguir". Otherwise, the plans text.
  @Input() canContinue = false;
  @Input() busy = false;
  @Output() continue = new EventEmitter<void>();

  readonly copy = CUT_COPY;
}
