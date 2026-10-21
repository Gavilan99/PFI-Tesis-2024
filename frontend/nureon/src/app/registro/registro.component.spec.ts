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
      { username: 'Persona', email: 'persona@example.test', password: 'Contraseña-1', consentAccepted: true },
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
