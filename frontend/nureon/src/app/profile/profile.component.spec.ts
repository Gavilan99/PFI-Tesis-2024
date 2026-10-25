import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Observable, of, throwError } from 'rxjs';
import { ProfileComponent } from './profile.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { ApiError } from '../core/services/api-error';
import { AuthService } from '../core/services/auth.service';
import { withEmptyProfile } from '../core/models/user.model';

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
