import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { LandingComponent } from './landing.component';
import { StartTestDialogComponent } from '../inicio/start-test-dialog/start-test-dialog.component';
import { API_SERVICE, ApiService } from '../core/services/api.service';
import { AuthService } from '../core/services/auth.service';
import { AccountType, User, withEmptyProfile } from '../core/models/user.model';
import { TestAttempt } from '../core/models/test-attempt.model';

function attempt(status: TestAttempt['status']): TestAttempt {
  return {
    id: 'attempt-1',
    userId: 'user-1',
    subjectId: null,
    tier: 'free_reduced',
    questionnaireVersion: 1,
    status,
    startedAt: '2026-01-01T00:00:00Z',
    completedAt: null,
    subjectLabel: null,
    subjectContext: null,
  };
}

describe('LandingComponent', () => {
  function create(user: User | null, latestAttempt: TestAttempt | null = null) {
    const api: Partial<ApiService> = { getLatestAttempt: () => of(latestAttempt), listSubjects: () => of([]) };
    TestBed.configureTestingModule({
      imports: [LandingComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: AuthService, useValue: { currentUserChanges: of(user) } },
      ],
    });
    const fixture = TestBed.createComponent(LandingComponent);
    fixture.detectChanges();
    return fixture;
  }

  function hero(fixture: ReturnType<typeof create>): HTMLElement {
    return (fixture.nativeElement as HTMLElement).querySelector('.hero')!;
  }

  function user(accountType: AccountType | null = 'individual'): User {
    return { ...withEmptyProfile({ id: 'user-1', displayName: 'Ana', email: 'ana@example.test' }), accountType };
  }

  it('invites to sign up without a session', () => {
    const fixture = create(null);
    const link = hero(fixture).querySelector('a')!;
    expect(link.textContent!.trim()).toBe('Empezar gratis');
    expect(link.getAttribute('href')).toBe('/registro');
  });

  it('greets the person and offers to start the test, with a link to the profile', () => {
    const fixture = create(user());
    const heroEl = hero(fixture);
    expect(heroEl.querySelector('h1')!.textContent).toContain('Hola, Ana');
    const testLink = heroEl.querySelector('a[href="/test"]') as HTMLAnchorElement;
    expect(testLink.textContent!.trim()).toBe('Empezar el test');
    const profileLink = heroEl.querySelector('a[href="/perfil"]') as HTMLAnchorElement;
    expect(profileLink.textContent!.trim()).toBe('Ir a mi perfil');
  });

  it('offers to continue, not restart, with an attempt in progress', () => {
    const fixture = create(user(), attempt('in_progress'));
    const testLink = hero(fixture).querySelector('a[href="/test"]') as HTMLAnchorElement;
    expect(testLink.textContent!.trim()).toBe('Continuar test');
  });

  it('opens the "¿Para quién es este test?" dialog for a salud/rrhh account starting fresh', () => {
    const fixture = create(user('salud'));
    const heroEl = hero(fixture);
    expect(heroEl.querySelector('a[href="/test"]')).toBeNull();
    const button = Array.from(heroEl.querySelectorAll('button')).find(
      (el) => el.textContent?.trim() === 'Empezar el test',
    ) as HTMLButtonElement;

    button.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.showStartTestDialog).toBeTrue();
    expect(fixture.debugElement.query((n) => n.componentInstance instanceof StartTestDialogComponent)).not.toBeNull();
  });

  it('resumes straight to /test for a salud/rrhh account with an attempt in progress, no dialog', () => {
    const fixture = create(user('salud'), attempt('in_progress'));
    const testLink = hero(fixture).querySelector('a[href="/test"]') as HTMLAnchorElement;
    expect(testLink.textContent!.trim()).toBe('Continuar test');
  });
});
