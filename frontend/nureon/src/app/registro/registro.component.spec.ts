import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { RegistroComponent } from './registro.component';
import { AuthService } from '../core/services/auth.service';
import { RegisterInput } from '../core/models/auth.model';
import { withEmptyProfile } from '../core/models/user.model';

const CONSENT_ERROR =
  'Para crear tu cuenta tenés que aceptar la Política de privacidad y los Términos y condiciones.';

describe('RegistroComponent, consent (Feature 11)', () => {
  let sent: RegisterInput[];

  function create() {
    sent = [];
    const auth: Partial<AuthService> = {
      register: (input: RegisterInput) => {
        sent.push(input);
        return of(withEmptyProfile({ id: 'user-1', displayName: input.username, email: input.email }));
      },
    };
    TestBed.configureTestingModule({
      imports: [RegistroComponent, NoopAnimationsModule],
      providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
    });
    const fixture = TestBed.createComponent(RegistroComponent);
    fixture.detectChanges();
    return fixture;
  }

  function fill(fixture: ReturnType<typeof create>) {
    fixture.componentInstance.form.patchValue({
      username: 'Persona',
      email: 'persona@example.test',
      password: 'Contraseña-1',
      accountType: 'individual',
    });
  }

  function submit(fixture: ReturnType<typeof create>) {
    (fixture.nativeElement as HTMLElement).querySelector('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  }

  function checkbox(fixture: ReturnType<typeof create>): HTMLInputElement {
    return (fixture.nativeElement as HTMLElement).querySelector('input[type="checkbox"]')!;
  }

  it('starts unchecked and shows the notice about the data and the United States', () => {
    const fixture = create();
    const text = (fixture.nativeElement as HTMLElement).textContent!;
    expect(checkbox(fixture).checked).toBeFalse();
    expect(text).toContain('Se guardan en servidores de Amazon Web Services en Estados Unidos.');
    expect(text).toContain('declaro ser mayor de 18 años');
    expect(text).toContain('consiento que mis datos se guarden en Estados Unidos');
  });

  it("doesn't send without the box checked, and shows the error next to it", () => {
    const fixture = create();
    fill(fixture);

    submit(fixture);

    expect(sent).toEqual([]);
    const error = (fixture.nativeElement as HTMLElement).querySelector('.registro-form__consent .registro-form__error');
    expect(error?.textContent?.trim()).toBe(CONSENT_ERROR);
  });

  it('sends exactly RegisterInput, consent included, once the box is checked', () => {
    const fixture = create();
    fill(fixture);
    checkbox(fixture).click();
    fixture.detectChanges();

    submit(fixture);

    expect(sent).toEqual([
      {
        username: 'Persona',
        email: 'persona@example.test',
        password: 'Contraseña-1',
        consentAccepted: true,
        accountType: 'individual',
      },
    ]);
  });

  it('links both texts, opening in another tab', () => {
    const fixture = create();
    const links = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLAnchorElement>('.registro-form__consent a'),
    ).map((a) => [a.textContent?.trim(), a.getAttribute('href'), a.target]);
    expect(links).toEqual([
      ['Política de privacidad', '/privacidad', '_blank'],
      ['Términos y condiciones', '/terminos', '_blank'],
    ]);
  });
});

describe('RegistroComponent, the required account type selector (Feature 21)', () => {
  let sent: RegisterInput[];

  function create() {
    sent = [];
    const auth: Partial<AuthService> = {
      register: (input: RegisterInput) => {
        sent.push(input);
        return of(withEmptyProfile({ id: 'user-1', displayName: input.username, email: input.email }));
      },
    };
    TestBed.configureTestingModule({
      imports: [RegistroComponent, NoopAnimationsModule],
      providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
    });
    const fixture = TestBed.createComponent(RegistroComponent);
    fixture.detectChanges();
    return fixture;
  }

  function fillWithoutAccountType(fixture: ReturnType<typeof create>) {
    fixture.componentInstance.form.patchValue({
      username: 'Persona',
      email: 'persona@example.test',
      password: 'Contraseña-1',
    });
    const checkbox = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      'input[type="checkbox"]',
    )!;
    checkbox.click();
    fixture.detectChanges();
  }

  function submit(fixture: ReturnType<typeof create>) {
    (fixture.nativeElement as HTMLElement).querySelector('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();
  }

  it('shows one explanatory line per account type', () => {
    const fixture = create();
    const text = (fixture.nativeElement as HTMLElement).textContent!;
    expect(text).toContain('Para conocerte a vos mismo o misma.');
    expect(text).toContain('Para evaluar a pacientes.');
    expect(text).toContain('Para evaluar a postulantes.');
  });

  it("doesn't send without an account type chosen", () => {
    const fixture = create();
    fillWithoutAccountType(fixture);

    submit(fixture);

    expect(sent).toEqual([]);
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('.registro-form__account-type .registro-form__error'),
    ).toBeTruthy();
  });

  it('sends the chosen account type once one is picked', () => {
    const fixture = create();
    fillWithoutAccountType(fixture);
    const radios = (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLInputElement>(
      'input[type="radio"]',
    );
    radios[1].click(); // salud, by ACCOUNT_TYPE_OPTIONS order
    fixture.detectChanges();

    submit(fixture);

    expect(sent.length).toBe(1);
    expect(sent[0].accountType).toBe('salud');
  });
});

describe('RegistroComponent, the post-registration step (Feature 21)', () => {
  function create() {
    const auth: Partial<AuthService> = {
      register: (input: RegisterInput) =>
        of(withEmptyProfile({ id: 'user-1', displayName: input.username, email: input.email })),
    };
    TestBed.configureTestingModule({
      imports: [RegistroComponent, NoopAnimationsModule],
      providers: [provideRouter([]), { provide: AuthService, useValue: auth }],
    });
    const fixture = TestBed.createComponent(RegistroComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('offers to complete the profile now or later instead of jumping to the test', () => {
    const fixture = create();
    fixture.componentInstance.form.patchValue({
      username: 'Persona',
      email: 'persona@example.test',
      password: 'Contraseña-1',
      accountType: 'individual',
    });
    const checkbox = (fixture.nativeElement as HTMLElement).querySelector<HTMLInputElement>(
      'input[type="checkbox"]',
    )!;
    checkbox.click();
    fixture.detectChanges();
    (fixture.nativeElement as HTMLElement).querySelector('form')!.dispatchEvent(new Event('submit'));
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent!;
    expect(text).toContain('Completar perfil');
    expect(text).toContain('Completar después');
    expect(text).not.toContain('Empezar el test');
  });
});
