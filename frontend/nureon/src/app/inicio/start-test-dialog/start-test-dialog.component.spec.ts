import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { StartTestDialogComponent } from './start-test-dialog.component';
import { API_SERVICE, ApiService } from '../../core/services/api.service';
import { AuthService } from '../../core/services/auth.service';
import { withEmptyProfile } from '../../core/models/user.model';
import { TestAttempt } from '../../core/models/test-attempt.model';
import { Subject, SubjectInput } from '../../core/models/subject.model';

const user = withEmptyProfile({ id: 'user-1', displayName: 'Profesional', email: 'pro@example.test' });

function attempt(id: string, overrides: Partial<TestAttempt> = {}): TestAttempt {
  return {
    id,
    userId: user.id,
    subjectId: null,
    tier: 'free_reduced',
    questionnaireVersion: 1,
    status: 'in_progress',
    startedAt: '2026-01-01T00:00:00.000Z',
    completedAt: null,
    subjectLabel: null,
    subjectContext: null,
    ...overrides,
  };
}

describe('StartTestDialogComponent (CU008)', () => {
  let createCalls: Array<{ userId: string; subject?: SubjectInput }>;

  function create(subjects: Subject[] = [], apiOverrides: Partial<ApiService> = {}) {
    createCalls = [];
    const api: Partial<ApiService> = {
      listSubjects: () => of(subjects),
      createTestAttempt: (userId: string, subject?: SubjectInput) => {
        createCalls.push({ userId, subject });
        return of(attempt('attempt-new', subject ? { subjectId: 'subject-x', subjectLabel: subject.label } : {}));
      },
      ...apiOverrides,
    };
    const auth: Partial<AuthService> = { currentUser: user };
    TestBed.configureTestingModule({
      imports: [StartTestDialogComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: auth },
      ],
    });
    const fixture = TestBed.createComponent(StartTestDialogComponent);
    fixture.detectChanges();
    return fixture;
  }

  function element(fixture: ReturnType<typeof create>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    document.body.style.overflow = '';
  });

  it('focuses the first field ("Para mí") on open', async () => {
    const fixture = create();
    await fixture.whenStable();
    const firstRadio = element(fixture).querySelector('input[type="radio"]');
    expect(document.activeElement).toBe(firstRadio);
  });

  it('starts for the account itself and navigates to /test with the new attempt id', () => {
    const fixture = create();
    const router = TestBed.inject(Router);
    const navigate = spyOn(router, 'navigateByUrl');

    fixture.componentInstance.startForSelf();

    expect(createCalls).toEqual([{ userId: user.id, subject: undefined }]);
    expect(navigate).toHaveBeenCalledWith('/test?intento=attempt-new');
  });

  it('requires the identifier and the consent for "Otra persona"', () => {
    const fixture = create();
    fixture.componentInstance.selectRecipient('other');
    fixture.detectChanges();

    fixture.componentInstance.startForOther();
    fixture.detectChanges();

    expect(createCalls).toEqual([]);
    const text = element(fixture).textContent!;
    expect(text).toContain('Ingresá un identificador.');
    expect(text).toContain('Declará que diste el consentimiento informado');
  });

  it('sends the identifier, context and consent for an evaluado, then navigates', () => {
    const fixture = create();
    const router = TestBed.inject(Router);
    const navigate = spyOn(router, 'navigateByUrl');
    fixture.componentInstance.selectRecipient('other');
    fixture.componentInstance.otherForm.setValue({
      label: 'Paciente A',
      context: 'Primera consulta',
      consentDeclared: true,
    });

    fixture.componentInstance.startForOther();

    expect(createCalls).toEqual([
      { userId: user.id, subject: { label: 'Paciente A', context: 'Primera consulta', consentDeclared: true } },
    ]);
    expect(navigate).toHaveBeenCalledWith('/test?intento=attempt-new');
  });

  it('precompletes the context when the identifier matches an existing evaluado, editable after', () => {
    const subjects: Subject[] = [
      { id: 'subject-1', label: 'Paciente A', testCount: 2, lastTestAt: '2026-01-01T00:00:00.000Z', lastTestContext: 'Terapia individual' },
    ];
    const fixture = create(subjects);
    fixture.componentInstance.selectRecipient('other');
    fixture.componentInstance.otherForm.controls.label.setValue('Paciente A');

    fixture.componentInstance.onLabelInput();

    expect(fixture.componentInstance.otherForm.controls.context.value).toBe('Terapia individual');

    // Editable afterward: typing in context doesn't get reset while the identifier still matches.
    fixture.componentInstance.otherForm.controls.context.setValue('Editado a mano');
    fixture.componentInstance.onLabelInput();
    expect(fixture.componentInstance.otherForm.controls.context.value).toBe('Editado a mano');
  });

  it('shows an inline error and stays open when starting the test fails', () => {
    const fixture = create([], { createTestAttempt: () => throwError(() => new Error('fail')) });

    fixture.componentInstance.startForSelf();
    fixture.detectChanges();

    expect(element(fixture).textContent).toContain('No pudimos empezar el test.');
  });

  it('emits closed on Escape and on a backdrop click', () => {
    const fixture = create();
    const closed = jasmine.createSpy('closed');
    fixture.componentInstance.closed.subscribe(closed);

    fixture.componentInstance.onEscape();
    expect(closed).toHaveBeenCalledTimes(1);

    element(fixture).querySelector<HTMLElement>('.start-test-dialog__backdrop')!.click();
    expect(closed).toHaveBeenCalledTimes(2);
  });

  it('locks the page behind it while open, and restores scrolling on close', () => {
    const fixture = create();
    expect(document.body.style.overflow).toBe('hidden');

    fixture.destroy();
    expect(document.body.style.overflow).toBe('');
  });
});
