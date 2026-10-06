import { Component, Inject } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';

// Simple contact form against MockApiService.submitContactMessage — same
// submitting/error/confirmation shape as RegistroComponent and
// FeedbackFormComponent, so it doesn't introduce a new pattern for the same
// kind of interaction.
@Component({
  selector: 'app-contacto',
  standalone: true,
  imports: [ReactiveFormsModule, MatInputModule, MatFormFieldModule, PageContainerComponent, BrandButtonComponent],
  templateUrl: './contacto.component.html',
  styleUrl: './contacto.component.scss',
})
export class ContactoComponent {
  readonly form = this.fb.group({
    name: ['', [Validators.required]],
    email: ['', [Validators.required, Validators.email]],
    message: ['', [Validators.required, Validators.minLength(10)]],
  });

  submitting = false;
  submitError: string | null = null;
  sent = false;

  constructor(
    private readonly fb: NonNullableFormBuilder,
    @Inject(API_SERVICE) private readonly api: ApiService,
  ) {}

  get nameError(): string | null {
    const control = this.form.controls.name;
    if (!control.touched || !control.invalid) return null;
    return 'Ingresá tu nombre.';
  }

  get emailError(): string | null {
    const control = this.form.controls.email;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Ingresá tu email.';
    if (control.hasError('email')) return 'Ingresá un email válido.';
    return null;
  }

  get messageError(): string | null {
    const control = this.form.controls.message;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Contanos en qué te podemos ayudar.';
    if (control.hasError('minlength')) return 'Un poco más de detalle nos ayuda a responder mejor.';
    return null;
  }

  onSubmit(): void {
    if (this.submitting) return;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting = true;
    this.submitError = null;
    this.api.submitContactMessage(this.form.getRawValue()).subscribe({
      next: () => {
        this.submitting = false;
        this.sent = true;
      },
      error: () => {
        this.submitting = false;
        this.submitError = 'No pudimos enviar tu mensaje. Probá de nuevo.';
      },
    });
  }
}
