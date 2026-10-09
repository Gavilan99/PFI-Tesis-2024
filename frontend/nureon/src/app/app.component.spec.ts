import { TestBed } from '@angular/core/testing';
import { AsyncPipe } from '@angular/common';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { Router, RouterModule } from '@angular/router';
import { of } from 'rxjs';
import { AppComponent } from './app.component';
import { routes } from './app-routing.module';
import { API_SERVICE, ApiService } from './core/services/api.service';
import { AuthService } from './core/services/auth.service';
import { withEmptyProfile } from './core/models/user.model';
import { HeaderComponent } from './shared/layout/header/header.component';
import { FooterComponent } from './shared/layout/footer/footer.component';

// AuthService persists the session here; cleared around each test so no
// session leaks into, or out of, the test run.
const AUTH_STORAGE_KEY = 'nureon_mock_auth_user';

// Only what the screens these tests visit actually call: sessionGuard asks for
// the latest attempt, /perfil for the history. Everything answers "nothing yet".
const apiStub: Partial<ApiService> = {
  getLatestAttempt: () => of(null),
  getAttemptHistory: () => of([]),
};

describe('AppComponent', () => {
  beforeEach(async () => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    await TestBed.configureTestingModule({
      imports: [RouterModule.forRoot(routes), NoopAnimationsModule, AsyncPipe, HeaderComponent, FooterComponent],
      declarations: [AppComponent],
      providers: [{ provide: API_SERVICE, useValue: apiStub }],
    }).compileComponents();
  });

  afterEach(() => {
    localStorage.removeItem(AUTH_STORAGE_KEY);
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('should render the header and the routed content', () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('app-header')).not.toBeNull();
    expect(compiled.querySelector('main router-outlet')).not.toBeNull();
  });

  describe('logout', () => {
    async function openLoggedIn(url: string) {
      const fixture = TestBed.createComponent(AppComponent);
      const router = TestBed.inject(Router);
      TestBed.inject(AuthService).setUser(
        withEmptyProfile({ id: 'user-1', displayName: 'Cuenta de prueba', email: 'prueba@example.test' }),
      );
      fixture.detectChanges();
      await router.navigateByUrl(url);
      await fixture.whenStable();
      fixture.detectChanges();
      return { fixture, router };
    }

    function clickLogout(fixture: ReturnType<typeof TestBed.createComponent<AppComponent>>) {
      const button = Array.from(
        (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>('app-header button'),
      ).find((b) => b.textContent?.includes('Cerrar sesión'));
      expect(button).withContext('"Cerrar sesión" in the header').toBeDefined();
      button!.click();
    }

    it('leaves a protected route for /ingresar', async () => {
      const { fixture, router } = await openLoggedIn('/perfil');
      expect(router.url).toBe('/perfil');

      clickLogout(fixture);
      await fixture.whenStable();
      fixture.detectChanges();

      expect(router.url).toBe('/ingresar');
      expect((fixture.nativeElement as HTMLElement).querySelector('app-profile')).toBeNull();
    });

    it('stays on a public route', async () => {
      const { fixture, router } = await openLoggedIn('/contacto');

      clickLogout(fixture);
      await fixture.whenStable();
      fixture.detectChanges();

      expect(router.url).toBe('/contacto');
    });
  });
});
