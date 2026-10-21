import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CutStatus } from '../../core/models/cut-status.model';
import { CUT_COPY } from '../../core/cuts/cut-copy';
import { CHANCE_ACCURACY, asPercent, hasNextCut } from '../../core/cuts/cut-plan';
import { BrandButtonComponent } from '../../shared/components/brand-button/brand-button.component';
import { FeedbackFormComponent } from '../../shared/components/feedback-form/feedback-form.component';

// Feature 10 — what /test shows after the last item of a cut that isn't the
// last one: the estimated accuracy of the cut just finished and of the next,
// and the choice between seeing the result now or going on. Without the
// paid tier the choice is the plans text instead. Only shows and emits: the
// test component closes or continues the attempt.
@Component({
  selector: 'app-between-cuts',
  standalone: true,
  imports: [BrandButtonComponent, FeedbackFormComponent],
  templateUrl: './between-cuts.component.html',
  styleUrl: './between-cuts.component.scss',
})
export class BetweenCutsComponent {
  @Input({ required: true }) status!: CutStatus;
  @Input() attemptId: string | null = null;
  // Continuing answered PAID_TIER_REQUIRED after the screen was drawn (the
  // subscription ran out in between): show the plans text from then on.
  @Input() paidTierRequired = false;
  @Input() busy = false;
  @Output() seeResult = new EventEmitter<void>();
  @Output() continue = new EventEmitter<void>();

  readonly copy = CUT_COPY;
  readonly chancePercent = asPercent(CHANCE_ACCURACY)!;

  get canContinue(): boolean {
    return hasNextCut(this.status) && this.status.canContinue && !this.paidTierRequired;
  }

  // In progress with the whole cut answered, the only thing that keeps an
  // attempt from going on is the tier (backend/docs/api-contract.md).
  get showPlans(): boolean {
    return hasNextCut(this.status) && !this.canContinue;
  }

  get moreItems(): number {
    return this.status.nextCutItems ?? 0;
  }

  get currentPercent(): number | null {
    return asPercent(this.status.currentCutAccuracy);
  }

  get nextPercent(): number | null {
    return asPercent(this.status.nextCutAccuracy);
  }
}
