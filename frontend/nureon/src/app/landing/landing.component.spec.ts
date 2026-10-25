import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { LandingComponent } from './landing.component';
import { AuthService } from '../core/services/auth.service';
import { User } from '../core/models/user.model';

describe('LandingComponent', () => {
  function heroOf(user: Partial<User> | null): HTMLElement {
    TestBed.configureTestingModule({
      imports: [LandingComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: { currentUserChanges: of(user) } },
      ],
    });
    const fixture = TestBed.createComponent(LandingComponent);
    fixture.detectChanges();
    return (fixture.nativeElement as HTMLElement).querySelector('.hero')!;
  }

  it('invites to sign up without a session', () => {
    const hero = heroOf(null);
    const link = hero.querySelector('a')!;
    expect(link.textContent!.trim()).toBe('Empezar gratis');
    expect(link.getAttribute('href')).toBe('/registro');
  });

  it('greets the person and points to the profile with a session', () => {
    const hero = heroOf({ id: 'user-1', displayName: 'Ana' });
    const link = hero.querySelector('a')!;
    expect(hero.querySelector('h1')!.textContent).toContain('Hola, Ana');
    expect(link.textContent!.trim()).toBe('Ir a mi perfil');
    expect(link.getAttribute('href')).toBe('/perfil');
    expect(hero.textContent).not.toContain('Empezar gratis');
  });
});
