import { Component, EventEmitter, Inject, Input, Output } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { API_SERVICE, ApiService } from '../../../core/services/api.service';
import { BrandButtonComponent } from '../brand-button/brand-button.component';

// Same limit the backend enforces (backend/app/blueprints/feedback/schemas.py,
// COMMENT_MAX_LENGTH): a longer comment is rejected there and the user only
// sees the generic error.
const COMMENT_MAX_LENGTH = 2000;

// RF06 — short on purpose: rating (1-5) + an optional comment. Used from
// TestComponent's closing screen (tied to the attempt just finished) and
// from ProfileComponent (general feedback, no attempt). Same component
// either way — only testAttemptId changes.
@Component({
  selector: 'app-feedback-form',
  standalone: true,
  imports: [ReactiveFormsModule, BrandButtonComponent],
  templateUrl: './feedback-form.component.html',
  styleUrl: './feedback-form.component.scss',
})
export class FeedbackFormComponent {
  @Input() testAttemptId: string | null = null;
  @Output() submitted = new EventEmitter<void>();

  readonly ratings = [1, 2, 3, 4, 5];
  readonly form = this.fb.group({
    rating: this.fb.control<number | null>(null, Validators.required),
    comment: ['', Validators.maxLength(COMMENT_MAX_LENGTH)],
  });

  submitting = false;
  error: string | null = null;
  sent = false;

  constructor(
    private readonly fb: NonNullableFormBuilder,
    @Inject(API_SERVICE) private readonly api: ApiService,
  ) {}

  get commentError(): string | null {
    const control = this.form.controls.comment;
    if (!control.touched || !control.hasError('maxlength')) return null;
    return `El comentario no puede superar los ${COMMENT_MAX_LENGTH.toLocaleString('es-AR')} caracteres.`;
  }

  selectRating(value: number): void {
    this.form.controls.rating.setValue(value);
  }

  onSubmit(): void {
    if (this.submitting) {
      return;
    }
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting = true;
    this.error = null;
    const { rating, comment } = this.form.getRawValue();
    this.api
      .submitFeedback({
        testAttemptId: this.testAttemptId,
        rating: rating!,
        comment: comment.trim() || null,
      })
      .subscribe({
        next: () => {
          this.submitting = false;
          this.sent = true;
          this.submitted.emit();
        },
        error: () => {
          this.submitting = false;
          this.error = 'No pudimos enviar tu comentario. Probá de nuevo.';
        },
      });
  }
}
