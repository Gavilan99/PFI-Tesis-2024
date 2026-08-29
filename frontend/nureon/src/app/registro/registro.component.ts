import { Component } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { AuthService } from '../core/services/auth.service';
import { User } from '../core/models/user.model';

// CU001 — Registrarse. One step, three fields (RF01), inline validation,
// and an on-screen confirmation (flow step 6) instead of a redirect.
// Errors (e.g. duplicate email) render inline in the form — never alert().
//
// mat-form-field/mat-error are used directly here, not through a wrapper
// component: MatFormField's MatFormFieldControl detection doesn't reliably
// find an <input matInput> projected through an intermediate component's
// own <ng-content> — confirmed via a live "mat-form-field must contain a
// MatFormFieldControl" runtime error. FormFieldComponent (Stage 3) is
// retired for the same reason.
@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatInputModule,
    MatFormFieldModule,
    PageContainerComponent,
    BrandButtonComponent,
  ],
  templateUrl: './registro.component.html',
  styleUrl: './registro.component.scss',
})
export class RegistroComponent {
  readonly form = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  submitting = false;
  submitError: string | null = null;
  registeredUser: User | null = null;

  constructor(
    private readonly fb: NonNullableFormBuilder,
    private readonly auth: AuthService,
  ) {}

  get usernameError(): string | null {
    const control = this.form.controls.username;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Ingresá un nombre de usuario.';
    if (control.hasError('minlength')) return 'Mínimo 3 caracteres.';
    return null;
  }

  get emailError(): string | null {
    const control = this.form.controls.email;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Ingresá tu email.';
    if (control.hasError('email')) return 'Ingresá un email válido.';
    return null;
  }

  get passwordError(): string | null {
    const control = this.form.controls.password;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Ingresá una contraseña.';
    if (control.hasError('minlength')) return 'Mínimo 8 caracteres.';
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
    this.auth.register(this.form.getRawValue()).subscribe({
      next: (user) => {
        this.submitting = false;
        this.registeredUser = user;
      },
      error: (err: Error) => {
        this.submitting = false;
        this.submitError = err.message;
      },
    });
  }
}
