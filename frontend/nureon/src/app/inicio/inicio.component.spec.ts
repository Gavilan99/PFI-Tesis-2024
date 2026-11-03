import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { InicioComponent } from './inicio.component';
import { StartTestDialogComponent } from './start-test-dialog/start-test-dialog.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { AuthService } from '../core/services/auth.service';
import { AccountType, withEmptyProfile } from '../core/models/user.model';

// CU008 (Feature 21): "Iniciar test" opens the "¿Para quién es este test?" dialog for salud/rrhh
// accounts, and keeps navigating straight to /test for individual ones, unchanged.
describe('InicioComponent, "Iniciar test" for salud/rrhh vs. individual accounts', () => {
  function create(accountType: AccountType) {
    const user = { ...withEmptyProfile({ id: 'user-1', displayName: 'Persona', email: 'p@example.test' }), accountType };
    const api: Partial<ApiService> = { getLatestAttempt: () => of(null), listSubjects: () => of([]) };
    const auth: Partial<AuthService> = { currentUser: user };
    TestBed.configureTestingModule({
      imports: [InicioComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: auth },
      ],
    });
    const fixture = TestBed.createComponent(InicioComponent);
    fixture.detectChanges();
    return fixture;
  }

  function element(fixture: ReturnType<typeof create>): HTMLElement {
    return fixture.nativeElement as HTMLElement;
  }

  function iniciarTestButton(fixture: ReturnType<typeof create>): HTMLElement {
    return Array.from(element(fixture).querySelectorAll('button, a')).find(
      (el) => el.textContent?.trim() === 'Iniciar test',
    ) as HTMLElement;
  }

  it('navigates straight to /test for an individual account, no dialog', () => {
    const fixture = create('individual');
    const button = iniciarTestButton(fixture);
    expect(button.tagName).toBe('A');
    expect(button.getAttribute('href')).toBe('/test');

    button.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.showStartTestDialog).toBeFalse();
    expect(fixture.debugElement.query((n) => n.componentInstance instanceof StartTestDialogComponent)).toBeNull();
  });

  it('opens the "¿Para quién es este test?" dialog for a salud account', () => {
    const fixture = create('salud');

    iniciarTestButton(fixture).click();
    fixture.detectChanges();

    expect(fixture.componentInstance.showStartTestDialog).toBeTrue();
    const dialog = fixture.debugElement.query((n) => n.componentInstance instanceof StartTestDialogComponent);
    expect(dialog).not.toBeNull();
    expect(element(fixture).textContent).toContain('¿Para quién es este test?');
  });

  it('opens the same dialog for a rrhh account', () => {
    const fixture = create('rrhh');

    iniciarTestButton(fixture).click();
    fixture.detectChanges();

    expect(fixture.componentInstance.showStartTestDialog).toBeTrue();
  });

  it('closes the dialog when it emits closed', () => {
    const fixture = create('salud');
    iniciarTestButton(fixture).click();
    fixture.detectChanges();

    fixture.componentInstance.closeStartTestDialog();
    fixture.detectChanges();

    expect(fixture.debugElement.query((n) => n.componentInstance instanceof StartTestDialogComponent)).toBeNull();
  });
});
