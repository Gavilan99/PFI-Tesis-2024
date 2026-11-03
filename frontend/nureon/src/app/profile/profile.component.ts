import { Component, Inject, OnInit } from '@angular/core';
import { DatePipe } from '@angular/common';
import { NonNullableFormBuilder, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { catchError, forkJoin, map, of, switchMap } from 'rxjs';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { AccountType } from '../core/models/user.model';
import { TestAttempt } from '../core/models/test-attempt.model';
import { Subject } from '../core/models/subject.model';
import { PageContainerComponent } from '../shared/layout/page-container/page-container.component';
import { EmptyStateComponent } from '../shared/components/empty-state/empty-state.component';
import { ErrorStateComponent } from '../shared/components/error-state/error-state.component';
import { LoadingStateComponent } from '../shared/components/loading-state/loading-state.component';
import { BrandButtonComponent } from '../shared/components/brand-button/brand-button.component';
import { FeedbackFormComponent } from '../shared/components/feedback-form/feedback-form.component';

interface HistoryEntry {
  attempt: TestAttempt;
  eneatype: number | null;
}

// Feature 20/21: one evaluado's row in the grouped history — its own attempts, grouped apart from
// "Mis tests", with the inline "Eliminar evaluado" confirmation's own open/busy/error state.
interface SubjectGroup {
  subject: Subject;
  lastEneatype: number | null;
  deleteOpen: boolean;
  deleting: boolean;
  deleteError: string | null;
}

const ACCOUNT_TYPE_LABEL: Record<AccountType, string> = {
  individual: 'Individual',
  salud: 'Salud mental',
  rrhh: 'RRHH',
};

const AGE_RANGES = ['18-24', '25-34', '35-44', '45-54', '55-64', '65 o más'];

const GENDERS = ['Femenino', 'Masculino', 'Prefiero no decir'];

const COUNTRIES = [
  'Argentina',
  'Bolivia',
  'Chile',
  'Colombia',
  'Costa Rica',
  'Cuba',
  'Ecuador',
  'El Salvador',
  'España',
  'Estados Unidos',
  'Guatemala',
  'Honduras',
  'México',
  'Nicaragua',
  'Panamá',
  'Paraguay',
  'Perú',
  'República Dominicana',
  'Uruguay',
  'Venezuela',
  'Otro',
];

// RF06 (comentarios), RF07 (perfil), RF08 (historial). The old ProfileComponent
// was an orphan — dialog markup, never routed or opened from anywhere. This
// is a screen at /perfil, not a dialog.
//
// Feature 11 adds "Borrar mi cuenta" (Ley 25.326 right of deletion, PA-7):
// an inline confirmation that says what is erased and what is kept
// anonymous, and only goes ahead once the account's email is typed. On
// success it goes to the landing with a message, then ends the session.
@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    DatePipe,
    PageContainerComponent,
    EmptyStateComponent,
    ErrorStateComponent,
    LoadingStateComponent,
    BrandButtonComponent,
    FeedbackFormComponent,
  ],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.scss',
})
export class ProfileComponent implements OnInit {
  readonly accountTypes: AccountType[] = ['individual', 'salud', 'rrhh'];
  readonly accountTypeLabel = ACCOUNT_TYPE_LABEL;
  readonly ageRanges = AGE_RANGES;
  readonly genders = GENDERS;
  readonly countries = COUNTRIES;

  readonly form = this.fb.group({
    displayName: [''],
    accountType: this.fb.control<AccountType | null>(null),
    ageRange: [''],
    gender: [''],
    country: [''],
    professionContext: [''],
  });

  saving = false;
  saveError: string | null = null;
  // ACCOUNT_TYPE_LOCKED (Feature 20/21): shown next to the selector instead of the generic
  // saveError, with the selector reverted to the account's current type.
  accountTypeError: string | null = null;
  saved = false;

  deleteOpen = false;
  deleting = false;
  deleteError: string | null = null;
  readonly deleteConfirmation = this.fb.control('');

  historyLoading = true;
  historyError: string | null = null;
  // The account's own attempts (every attempt, for an individual account; just the ones without
  // an evaluado, for salud/rrhh — see isProfessional/subjectGroups below).
  history: HistoryEntry[] = [];
  subjectGroups: SubjectGroup[] = [];

  constructor(
    private readonly fb: NonNullableFormBuilder,
    @Inject(API_SERVICE) private readonly api: ApiService,
    private readonly auth: AuthService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    const user = this.auth.currentUser;
    if (user) {
      this.form.patchValue({
        displayName: user.displayName,
        accountType: user.accountType,
        ageRange: user.ageRange ?? '',
        gender: user.gender ?? '',
        country: user.country ?? '',
        professionContext: user.professionContext ?? '',
      });
    }
    this.loadHistory();
  }

  onSave(): void {
    if (this.saving) {
      return;
    }
    this.saving = true;
    this.saveError = null;
    this.accountTypeError = null;
    this.saved = false;
    const previousAccountType = this.auth.currentUser?.accountType ?? null;
    const raw = this.form.getRawValue();
    this.auth
      .updateProfile({
        displayName: raw.displayName,
        accountType: raw.accountType,
        ageRange: raw.ageRange || null,
        gender: raw.gender || null,
        country: raw.country || null,
        professionContext: raw.professionContext || null,
      })
      .subscribe({
        next: () => {
          this.saving = false;
          this.saved = true;
        },
        error: (err: unknown) => {
          this.saving = false;
          // The account has active evaluados: their consent and personalization are tied to the
          // type, so it's reverted instead of left showing a change that didn't save.
          if (err instanceof ApiError && err.code === 'ACCOUNT_TYPE_LOCKED') {
            this.accountTypeError = err.message;
            this.form.controls.accountType.setValue(previousAccountType);
            return;
          }
          this.saveError = 'No pudimos guardar los cambios. Probá de nuevo.';
        },
      });
  }

  get accountEmail(): string {
    return this.auth.currentUser?.email ?? '';
  }

  // Feature 20/21: salud/rrhh accounts administer the test to evaluados — their history groups
  // separately (loadHistory) and "Iniciar test" (inicio) offers to test someone else.
  get isProfessional(): boolean {
    const type = this.auth.currentUser?.accountType;
    return type === 'salud' || type === 'rrhh';
  }

  get deleteConfirmed(): boolean {
    const typed = this.deleteConfirmation.value.trim().toLowerCase();
    return typed !== '' && typed === this.accountEmail.toLowerCase();
  }

  openDelete(): void {
    this.deleteOpen = true;
    this.deleteError = null;
    this.deleteConfirmation.setValue('');
  }

  cancelDelete(): void {
    this.deleteOpen = false;
    this.deleteError = null;
  }

  onDelete(): void {
    if (this.deleting || !this.deleteConfirmed) {
      return;
    }
    this.deleting = true;
    this.deleteError = null;
    this.auth.deleteAccount().subscribe({
      next: () => {
        // Leave /perfil first: ending the session here would send it through
        // sessionGuard to /ingresar instead of the landing.
        this.router
          .navigateByUrl('/', { state: { accountDeleted: true } })
          .finally(() => this.auth.logout());
      },
      error: (err: Error) => {
        this.deleting = false;
        this.deleteError = err.message || 'No pudimos borrar tu cuenta. Probá de nuevo.';
      },
    });
  }

  retryHistory(): void {
    this.loadHistory();
  }

  openDeleteSubject(group: SubjectGroup): void {
    group.deleteOpen = true;
    group.deleteError = null;
  }

  cancelDeleteSubject(group: SubjectGroup): void {
    group.deleteOpen = false;
    group.deleteError = null;
  }

  // Logical deletion (Ley 25.326): the identifier and the declared context are erased, the
  // evaluado's attempts and results stay, anonymous — same as deleting the account itself, scoped
  // to one evaluado. The group disappears from the list; its own past attempts aren't reloaded,
  // same as "Mis tests" never refetching after a completed one changes nothing about it.
  confirmDeleteSubject(group: SubjectGroup): void {
    if (group.deleting) {
      return;
    }
    group.deleting = true;
    group.deleteError = null;
    this.api.deleteSubject(group.subject.id).subscribe({
      next: () => {
        this.subjectGroups = this.subjectGroups.filter((g) => g !== group);
      },
      error: (err: Error) => {
        group.deleting = false;
        group.deleteError = err.message || 'No pudimos eliminar al evaluado.';
      },
    });
  }

  private loadHistory(): void {
    this.historyLoading = true;
    this.historyError = null;
    const userId = this.auth.currentUser?.id;
    if (!userId) {
      this.history = [];
      this.subjectGroups = [];
      this.historyLoading = false;
      return;
    }
    const isProfessional = this.isProfessional;
    forkJoin({
      attempts: this.api.getAttemptHistory(userId),
      subjects: isProfessional ? this.api.listSubjects() : of<Subject[]>([]),
    })
      .pipe(
        switchMap(({ attempts, subjects }) => {
          const completed = attempts.filter((a) => a.status === 'completed');
          if (completed.length === 0) {
            return of({ attempts, subjects, eneatypeByAttempt: new Map<string, number | null>() });
          }
          // Each fetch is independently resilient: one attempt with a missing/
          // corrupted result (e.g. simulated via nureonDev.breakResultLoading())
          // must not blank out every OTHER attempt's result — forkJoin as a
          // whole errors if any single inner observable does, so each one
          // catches its own failure instead of propagating it.
          return forkJoin(
            completed.map((a) =>
              this.api.getResult(a.id).pipe(
                map((result) => ({ attemptId: a.id, eneatype: result.eneatype as number | null })),
                catchError(() => of({ attemptId: a.id, eneatype: null })),
              ),
            ),
          ).pipe(
            map((results) => ({
              attempts,
              subjects,
              eneatypeByAttempt: new Map(results.map((r) => [r.attemptId, r.eneatype])),
            })),
          );
        }),
      )
      .subscribe({
        next: ({ attempts, subjects, eneatypeByAttempt }) => {
          // A salud/rrhh account's own attempts are the ones with no evaluado; an individual
          // account's attempts never have one, so this is a no-op filter for it.
          const ownAttempts = isProfessional ? attempts.filter((a) => a.subjectId === null) : attempts;
          this.history = ownAttempts.map((attempt) => ({
            attempt,
            eneatype: eneatypeByAttempt.get(attempt.id) ?? null,
          }));
          this.subjectGroups = subjects.map((subject) => {
            const lastCompleted = attempts
              .filter((a) => a.subjectId === subject.id && a.status === 'completed' && a.completedAt)
              .sort((a, b) => new Date(b.completedAt!).getTime() - new Date(a.completedAt!).getTime())[0];
            return {
              subject,
              lastEneatype: lastCompleted ? eneatypeByAttempt.get(lastCompleted.id) ?? null : null,
              deleteOpen: false,
              deleting: false,
              deleteError: null,
            };
          });
          this.historyLoading = false;
        },
        error: () => {
          this.historyLoading = false;
          this.historyError = 'No pudimos cargar tu historial.';
        },
      });
  }
}
