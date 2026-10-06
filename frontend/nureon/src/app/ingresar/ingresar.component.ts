import { Component } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { Router, RouterLink } from '@angular/router';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { AuthService } from '../core/services/auth.service';

// CU002 — Iniciar sesión. Password recovery and the Google/Facebook slots
// are drawn but inert — RNF09 wires them up once Cognito exists. Errors
// render inline in the form, never alert().
//
// mat-form-field/mat-error used directly, not through a wrapper component —
// see the comment in RegistroComponent for why (MatFormFieldControl
// detection doesn't reliably reach through an intermediate ng-content).
@Component({
  selector: 'app-ingresar',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    MatInputModule,
    MatFormFieldModule,
    RouterLink,
    PageContainerComponent,
    BrandButtonComponent,
  ],
  templateUrl: './ingresar.component.html',
  styleUrl: './ingresar.component.scss',
})
export class IngresarComponent {
  readonly form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  submitting = false;
  submitError: string | null = null;

  constructor(
    private readonly fb: NonNullableFormBuilder,
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

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
    if (control.hasError('required')) return 'Ingresá tu contraseña.';
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
    this.auth.login(this.form.getRawValue()).subscribe({
      next: () => {
        this.submitting = false;
        this.router.navigateByUrl('/inicio');
      },
      error: (err: Error) => {
        this.submitting = false;
        this.submitError = err.message;
      },
    });
  }
}
