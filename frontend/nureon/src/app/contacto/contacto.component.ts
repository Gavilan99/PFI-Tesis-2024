import { Component, Inject } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';

// Same limits the backend enforces (backend/app/blueprints/feedback/schemas.py):
// a longer value is rejected there and the user only sees the generic error.
const CONTACT_NAME_MAX_LENGTH = 100;
const CONTACT_EMAIL_MAX_LENGTH = 254;
const CONTACT_MESSAGE_MAX_LENGTH = 5000;

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
    name: ['', [Validators.required, Validators.maxLength(CONTACT_NAME_MAX_LENGTH)]],
    email: ['', [Validators.required, Validators.email, Validators.maxLength(CONTACT_EMAIL_MAX_LENGTH)]],
    message: [
      '',
      [Validators.required, Validators.minLength(10), Validators.maxLength(CONTACT_MESSAGE_MAX_LENGTH)],
    ],
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
    if (control.hasError('maxlength')) return `El nombre no puede superar los ${CONTACT_NAME_MAX_LENGTH} caracteres.`;
    return 'Ingresá tu nombre.';
  }

  get emailError(): string | null {
    const control = this.form.controls.email;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Ingresá tu email.';
    // Before 'email': Angular's email validator also rejects addresses this
    // long, and "inválido" wouldn't tell the user what to fix.
    if (control.hasError('maxlength')) return `El email no puede superar los ${CONTACT_EMAIL_MAX_LENGTH} caracteres.`;
    if (control.hasError('email')) return 'Ingresá un email válido.';
    return null;
  }

  get messageError(): string | null {
    const control = this.form.controls.message;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Contanos en qué te podemos ayudar.';
    if (control.hasError('minlength')) return 'Un poco más de detalle nos ayuda a responder mejor.';
    if (control.hasError('maxlength'))
      return `El mensaje no puede superar los ${CONTACT_MESSAGE_MAX_LENGTH.toLocaleString('es-AR')} caracteres.`;
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
