import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Observable, of, throwError } from 'rxjs';
import { ProfileComponent } from './profile.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { AccountType, withEmptyProfile } from '../core/models/user.model';
import { TestAttempt } from '../core/models/test-attempt.model';
import { Subject } from '../core/models/subject.model';

const user = withEmptyProfile({ id: 'user-1', displayName: 'Persona', email: 'persona@example.test' });

describe('ProfileComponent, deleting the account (Feature 11)', () => {
  let calls: string[];

  function create(deleteResult: Observable<void>) {
    calls = [];
    const api: Partial<ApiService> = { getAttemptHistory: () => of([]) };
    const auth: Partial<AuthService> = {
      currentUser: user,
      deleteAccount: () => {
        calls.push('deleteAccount');
        return deleteResult;
      },
      logout: () => {
        calls.push('logout');
      },
    };
    TestBed.configureTestingModule({
      imports: [ProfileComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: auth },
      ],
    });
    const fixture = TestBed.createComponent(ProfileComponent);
    fixture.detectChanges();
    return fixture;
  }

  function element(fixture: ReturnType<typeof create>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function open(fixture: ReturnType<typeof create>) {
    const button = Array.from(element(fixture).querySelectorAll('.profile__delete button')).find(
      (b) => b.textContent?.trim() === 'Borrar mi cuenta',
    ) as HTMLButtonElement;
    button.click();
    fixture.detectChanges();
  }

  function type(fixture: ReturnType<typeof create>, value: string) {
    const input = element(fixture).querySelector<HTMLInputElement>('.profile__delete-panel input')!;
    input.value = value;
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  }

  function confirmButton(fixture: ReturnType<typeof create>): HTMLButtonElement {
    return element(fixture).querySelector('.profile__delete-confirm')!;
  }

  it('says what is erased and what is kept before asking for the email', () => {
    const fixture = create(of(undefined));
    open(fixture);
    const text = element(fixture).querySelector('.profile__delete-panel')!.textContent!;
    expect(text).toContain('Se borra:');
    expect(text).toContain('Se conserva, sin tu nombre ni tu email');
    expect(text).toContain('persona@example.test');
  });

  it('only enables the deletion once the account email is typed', () => {
    const fixture = create(of(undefined));
    open(fixture);
    expect(confirmButton(fixture).disabled).toBeTrue();

    type(fixture, 'otra@example.test');
    expect(confirmButton(fixture).disabled).toBeTrue();

    type(fixture, ' Persona@Example.test ');
    expect(confirmButton(fixture).disabled).toBeFalse();
  });

  it('deletes, goes to the landing with the notice, then ends the session', async () => {
    const fixture = create(of(undefined));
    const router = TestBed.inject(Router);
    const navigate = spyOn(router, 'navigateByUrl').and.callFake(() => {
      calls.push('navigate');
      return Promise.resolve(true);
    });
    open(fixture);
    type(fixture, 'persona@example.test');

    confirmButton(fixture).click();
    await fixture.whenStable();

    expect(navigate).toHaveBeenCalledWith('/', { state: { accountDeleted: true } });
    expect(calls).toEqual(['deleteAccount', 'navigate', 'logout']);
  });

  it('keeps the session and shows the error when the deletion fails', () => {
    const message = 'El servicio de cuentas no está disponible. Probá de nuevo en unos minutos.';
    const fixture = create(throwError(() => new ApiError(message, 'IDENTITY_UNAVAILABLE', 503)));
    open(fixture);
    type(fixture, 'persona@example.test');

    confirmButton(fixture).click();
    fixture.detectChanges();

    expect(calls).toEqual(['deleteAccount']);
    expect(element(fixture).querySelector('.profile__delete-panel .profile__error')?.textContent?.trim()).toBe(message);
    expect(confirmButton(fixture).disabled).toBeFalse();
  });
});

// Feature 21 reverts Fix #53's rrhh-specific label: every account type shares the same field,
// "Contexto profesional" / "ej. Psicóloga clínica" — the rrhh-aware personalization stays (it just
// no longer has its own label in the profile).
describe('ProfileComponent, the professionContext field label and placeholder', () => {
  function create() {
    const api: Partial<ApiService> = { getAttemptHistory: () => of([]) };
    const auth: Partial<AuthService> = { currentUser: user };
    TestBed.configureTestingModule({
      imports: [ProfileComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: auth },
      ],
    });
    const fixture = TestBed.createComponent(ProfileComponent);
    fixture.detectChanges();
    return fixture;
  }

  function element(fixture: ReturnType<typeof create>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function professionField(fixture: ReturnType<typeof create>) {
    const label = Array.from(element(fixture).querySelectorAll('.profile__field span')).find((span) =>
      span.textContent?.includes('Contexto profesional'),
    );
    const input = label?.closest('.profile__field')?.querySelector('input') as HTMLInputElement | undefined;
    return { labelText: label?.textContent?.trim(), input };
  }

  // The selector binds its options with [ngValue], so a real <select> change event drives this
  // same form control — this sets it the same way the user's click would, without going through
  // Angular's internal index-based option values.
  function selectAccountType(fixture: ReturnType<typeof create>, value: AccountType | null) {
    fixture.componentInstance.form.controls.accountType.setValue(value);
    fixture.detectChanges();
  }

  it('shows the same label and placeholder for rrhh as for any other type', () => {
    const fixture = create();
    selectAccountType(fixture, 'rrhh');

    const { labelText, input } = professionField(fixture);
    expect(labelText).toBe('Contexto profesional');
    expect(input?.placeholder).toBe('ej. Psicóloga clínica');
  });

  it('shows the same label and placeholder for salud', () => {
    const fixture = create();
    selectAccountType(fixture, 'salud');

    const { labelText, input } = professionField(fixture);
    expect(labelText).toBe('Contexto profesional');
    expect(input?.placeholder).toBe('ej. Psicóloga clínica');
  });

  it('hides the field entirely for individual, unchanged from before', () => {
    const fixture = create();
    selectAccountType(fixture, 'individual');

    expect(professionField(fixture).input).toBeUndefined();
  });

  it('keeps the same label and placeholder with no account type selected', () => {
    const fixture = create();
    selectAccountType(fixture, null);

    const { labelText, input } = professionField(fixture);
    expect(labelText).toBe('Contexto profesional');
    expect(input?.placeholder).toBe('ej. Psicóloga clínica');
  });
});

describe('ProfileComponent, changing the account type (Feature 20/21)', () => {
  function create(updateProfile: (input: unknown) => Observable<unknown>) {
    const api: Partial<ApiService> = { getAttemptHistory: () => of([]) };
    const auth: Partial<AuthService> = {
      currentUser: { ...user, accountType: 'individual' },
      updateProfile: updateProfile as unknown as AuthService['updateProfile'],
    };
    TestBed.configureTestingModule({
      imports: [ProfileComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: auth },
      ],
    });
    const fixture = TestBed.createComponent(ProfileComponent);
    fixture.detectChanges();
    return fixture;
  }

  function save(fixture: ReturnType<typeof create>) {
    (fixture.nativeElement as HTMLElement).querySelector('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  }

  it('shows the message next to the selector and reverts the value on ACCOUNT_TYPE_LOCKED', () => {
    const message = 'No podés cambiar el tipo de cuenta mientras tengas evaluados activos.';
    const fixture = create(() => throwError(() => new ApiError(message, 'ACCOUNT_TYPE_LOCKED', 409)));
    fixture.componentInstance.form.controls.accountType.setValue('salud');

    save(fixture);

    expect(fixture.componentInstance.form.controls.accountType.value).toBe('individual');
    const error = (fixture.nativeElement as HTMLElement).querySelector('.profile__form .profile__error');
    expect(error?.textContent?.trim()).toBe(message);
  });

  it('saves normally when the account has no active evaluados', () => {
    const fixture = create(() => of({ ...user, accountType: 'salud' }));
    fixture.componentInstance.form.controls.accountType.setValue('salud');

    save(fixture);

    expect(fixture.componentInstance.saved).toBeTrue();
    expect(fixture.componentInstance.accountTypeError).toBeNull();
  });
});

describe('ProfileComponent, the grouped history for salud/rrhh accounts (Feature 20/21)', () => {
  const ownAttempt: TestAttempt = {
    id: 'attempt-own',
    userId: user.id,
    subjectId: null,
    tier: 'free_reduced',
    questionnaireVersion: 1,
    status: 'completed',
    startedAt: '2026-01-01T00:00:00.000Z',
    completedAt: '2026-01-01T00:10:00.000Z',
    subjectLabel: null,
    subjectContext: null,
  };
  const subjectAttempt: TestAttempt = {
    id: 'attempt-subject',
    userId: user.id,
    subjectId: 'subject-1',
    tier: 'free_reduced',
    questionnaireVersion: 1,
    status: 'completed',
    startedAt: '2026-01-02T00:00:00.000Z',
    completedAt: '2026-01-02T00:10:00.000Z',
    subjectLabel: 'Paciente A',
    subjectContext: 'Terapia individual',
  };
  const subject: Subject = {
    id: 'subject-1',
    label: 'Paciente A',
    testCount: 1,
    lastTestAt: subjectAttempt.completedAt,
    lastTestContext: subjectAttempt.subjectContext,
  };

  function create(deleteResult: Observable<void> = of(undefined)) {
    const deleteCalls: string[] = [];
    const api: Partial<ApiService> = {
      getAttemptHistory: () => of([subjectAttempt, ownAttempt]),
      listSubjects: () => of([subject]),
      getResult: (attemptId: string) =>
        of({
          id: `result-${attemptId}`,
          testAttemptId: attemptId,
          eneatype: attemptId === ownAttempt.id ? 4 : 7,
          descriptionText: '',
          generatedAt: '2026-01-01T00:10:00.000Z',
        }),
      deleteSubject: (subjectId: string) => {
        deleteCalls.push(subjectId);
        return deleteResult;
      },
    };
    const auth: Partial<AuthService> = { currentUser: { ...user, accountType: 'salud' } };
    TestBed.configureTestingModule({
      imports: [ProfileComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: auth },
      ],
    });
    const fixture = TestBed.createComponent(ProfileComponent);
    fixture.detectChanges();
    return { fixture, deleteCalls };
  }

  function element(fixture: ReturnType<typeof create>['fixture']): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  it('splits "Mis tests" from the evaluado, with its test count and last result', () => {
    const { fixture } = create();
    const text = element(fixture).textContent!;

    expect(text).toContain('Mis tests');
    expect(text).toContain('Eneatipo 4');
    expect(text).toContain('Paciente A');
    expect(text).toContain('1 test');
    expect(text).toContain('Eneatipo 7');
    expect(fixture.componentInstance.history.length).toBe(1);
    expect(fixture.componentInstance.history[0].attempt.id).toBe(ownAttempt.id);
  });

  it('deletes the evaluado after the confirmation, removing its group', () => {
    const { fixture, deleteCalls } = create();
    fixture.componentInstance.openDeleteSubject(fixture.componentInstance.subjectGroups[0]);
    fixture.detectChanges();
    expect(element(fixture).textContent).toContain('Se borran el identificador y el contexto');

    fixture.componentInstance.confirmDeleteSubject(fixture.componentInstance.subjectGroups[0]);
    fixture.detectChanges();

    expect(deleteCalls).toEqual(['subject-1']);
    expect(fixture.componentInstance.subjectGroups.length).toBe(0);
  });

  it('keeps the group and shows the error when the deletion fails', () => {
    const { fixture } = create(throwError(() => new Error('No pudimos eliminar al evaluado.')));
    const group = fixture.componentInstance.subjectGroups[0];
    fixture.componentInstance.openDeleteSubject(group);

    fixture.componentInstance.confirmDeleteSubject(group);
    fixture.detectChanges();

    expect(fixture.componentInstance.subjectGroups.length).toBe(1);
    expect(group.deleteError).toBe('No pudimos eliminar al evaluado.');
  });
});
