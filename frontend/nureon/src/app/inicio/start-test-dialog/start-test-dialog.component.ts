import {
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Inject,
  OnDestroy,
  OnInit,
  Output,
  ViewChild,
} from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { API_SERVICE, ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { Subject } from '../../core/models/subject.model';
import { BrandButtonComponent } from '../../shared/components/brand-button/brand-button.component';

type Recipient = 'self' | 'other';

// CU008 — "¿Para quién es este test?", opened from /inicio's "Iniciar test" for a salud/rrhh
// account: administers the test to the account itself, as before, or to an evaluado. Self-contained
// modal, same convention as FreemiumInfoDialogComponent — captures focus on init and restores it on
// destroy, closes on Escape or a backdrop click, locks page scroll while open.
@Component({
  selector: 'app-start-test-dialog',
  standalone: true,
  imports: [ReactiveFormsModule, BrandButtonComponent],
  templateUrl: './start-test-dialog.component.html',
  styleUrl: './start-test-dialog.component.scss',
})
export class StartTestDialogComponent implements OnInit, OnDestroy {
  @Output() closed = new EventEmitter<void>();
  @ViewChild('firstField') private firstFieldRef?: ElementRef<HTMLElement>;
  private focusedElementBeforeOpen: HTMLElement | null = null;

  recipient: Recipient = 'self';
  subjects: Subject[] = [];
  private lastMatchedSubjectId: string | null = null;

  readonly otherForm = this.fb.group({
    label: ['', [Validators.required, Validators.maxLength(64)]],
    context: ['', [Validators.maxLength(255)]],
    consentDeclared: [false, Validators.requiredTrue],
  });

  submitting = false;
  submitError: string | null = null;

  constructor(
    private readonly fb: NonNullableFormBuilder,
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.focusedElementBeforeOpen = document.activeElement as HTMLElement | null;
    setTimeout(() => this.firstFieldRef?.nativeElement.focus());
    // A backdrop alone doesn't stop the page behind it from scrolling.
    document.body.style.overflow = 'hidden';
    // Only a salud/rrhh account ever opens this dialog, but a failed fetch just means no
    // autocomplete/precompleted context — never blocks picking "Otra persona" by hand.
    this.api.listSubjects().subscribe({
      next: (subjects) => (this.subjects = subjects),
      error: () => (this.subjects = []),
    });
  }

  ngOnDestroy(): void {
    document.body.style.overflow = '';
    this.focusedElementBeforeOpen?.focus();
  }

  close(): void {
    this.closed.emit();
  }

  @HostListener('window:keydown.escape')
  onEscape(): void {
    this.close();
  }

  selectRecipient(recipient: Recipient): void {
    this.recipient = recipient;
    this.submitError = null;
  }

  get labelError(): string | null {
    const control = this.otherForm.controls.label;
    if (!control.touched || !control.invalid) return null;
    if (control.hasError('required')) return 'Ingresá un identificador.';
    return 'Máximo 64 caracteres.';
  }

  get consentError(): string | null {
    const control = this.otherForm.controls.consentDeclared;
    if (!control.touched || !control.invalid) return null;
    return 'Declará que diste el consentimiento informado para continuar.';
  }

  // Precompletes the context from the matching evaluado's last test, editable afterward — only
  // when the match actually changes, so editing the context itself doesn't keep resetting it.
  onLabelInput(): void {
    const typed = this.otherForm.controls.label.value.trim().toLowerCase();
    const match = this.subjects.find((s) => s.label.toLowerCase() === typed);
    const matchedId = match?.id ?? null;
    if (matchedId !== this.lastMatchedSubjectId) {
      this.lastMatchedSubjectId = matchedId;
      if (match) {
        this.otherForm.controls.context.setValue(match.lastTestContext ?? '');
      }
    }
  }

  startForSelf(): void {
    if (this.submitting) {
      return;
    }
    const userId = this.auth.currentUser?.id;
    if (!userId) {
      return;
    }
    this.submitting = true;
    this.submitError = null;
    this.api.createTestAttempt(userId).subscribe({
      next: (attempt) => this.router.navigateByUrl(`/test?intento=${attempt.id}`),
      error: () => {
        this.submitting = false;
        this.submitError = 'No pudimos empezar el test. Probá de nuevo.';
      },
    });
  }

  startForOther(): void {
    if (this.submitting) {
      return;
    }
    if (this.otherForm.invalid) {
      this.otherForm.markAllAsTouched();
      return;
    }
    const userId = this.auth.currentUser?.id;
    if (!userId) {
      return;
    }
    this.submitting = true;
    this.submitError = null;
    const raw = this.otherForm.getRawValue();
    this.api
      .createTestAttempt(userId, {
        label: raw.label.trim(),
        context: raw.context.trim() || null,
        consentDeclared: raw.consentDeclared,
      })
      .subscribe({
        next: (attempt) => this.router.navigateByUrl(`/test?intento=${attempt.id}`),
        error: () => {
          this.submitting = false;
          this.submitError = 'No pudimos empezar el test. Probá de nuevo.';
        },
      });
  }
}
