import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';
import { routes } from '../../app-routing.module';
import { AuthService } from '../../core/services/auth.service';
import { User } from '../../core/models/user.model';
import { ENEATYPE_CONTENT, ENEATYPE_NUMBERS } from '../../resultados/eneatype-content';

// Runs against the app's real route config, so it covers the guard, the
// title resolver and the lazy load, not just the component.
describe('EneatypePageComponent', () => {
  async function setUp(user: Partial<User> | null = null): Promise<RouterTestingHarness> {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [
        provideRouter(routes),
        { provide: AuthService, useValue: { currentUserChanges: of(user) } },
      ],
    });
    return RouterTestingHarness.create();
  }

  for (const invalid of ['0', '10', 'abc']) {
    it(`redirects /eneagrama/${invalid} to /eneagrama`, async () => {
      const harness = await setUp();
      await harness.navigateByUrl(`/eneagrama/${invalid}`);
      expect(TestBed.inject(Router).url).toBe('/eneagrama');
    });
  }

  for (const eneatype of ENEATYPE_NUMBERS) {
    it(`renders eneatype ${eneatype} with its title and the four sections`, async () => {
      const harness = await setUp();
      await harness.navigateByUrl(`/eneagrama/${eneatype}`);
      const page = harness.routeNativeElement!;
      const label = `Eneatipo ${eneatype} — ${ENEATYPE_CONTENT[eneatype].title}`;
      expect(page.querySelector('h1')!.textContent!.trim()).toBe(label);
      const sections = Array.from(page.querySelectorAll('.eneatype__section h2')).map((h) => h.textContent!.trim());
      expect(sections).toEqual(['Fortalezas', 'Debilidades', 'Crecimiento', 'Tensiones']);
      const items = Array.from(page.querySelectorAll('.eneatype__section li')).map((li) => li.textContent!.trim());
      const { strengths, weaknesses, growth, tensions } = ENEATYPE_CONTENT[eneatype].page;
      expect(items).toEqual([...strengths, ...weaknesses, ...growth, ...tensions]);
      expect(TestBed.inject(Router).routerState.snapshot.root.firstChild!.data['title']).toBe(label);
    });
  }

  it('links to the previous and next types, wrapping around at 1 and 9', async () => {
    const harness = await setUp();
    await harness.navigateByUrl('/eneagrama/9');
    const nav = () => Array.from(harness.routeNativeElement!.querySelectorAll('.eneatype__nav a'));
    expect(nav().map((a) => a.getAttribute('href'))).toEqual(['/eneagrama/8', '/eneagrama/1']);
    await harness.navigateByUrl('/eneagrama/1');
    expect(nav().map((a) => a.getAttribute('href'))).toEqual(['/eneagrama/9', '/eneagrama/2']);
  });

  it('names the types growth and stress lead to, along the enneagram lines', async () => {
    const harness = await setUp();
    await harness.navigateByUrl('/eneagrama/1');
    const lines = Array.from(harness.routeNativeElement!.querySelectorAll('.eneatype__line strong'));
    expect(lines.map((line) => line.textContent!.trim())).toEqual([
      'Eneatipo 7 — El Entusiasta',
      'Eneatipo 4 — El Individualista',
    ]);
  });

  // Opened from a shared link, the page keeps the browser's starting point;
  // reached from inside the app, focus moves to the new heading.
  it('focuses the heading only after an in-app navigation', async () => {
    TestBed.configureTestingModule({
      imports: [NoopAnimationsModule],
      providers: [provideRouter(routes), { provide: AuthService, useValue: { currentUserChanges: of(null) } }],
    });
    const harness = await RouterTestingHarness.create('/eneagrama/4');
    await new Promise((resolve) => setTimeout(resolve));
    const heading = () => harness.routeNativeElement!.querySelector('h1');
    expect(document.activeElement).not.toBe(heading());

    await harness.navigateByUrl('/eneagrama/5');
    await new Promise((resolve) => setTimeout(resolve));
    expect(document.activeElement).toBe(heading());
  });

  // RouterLink on the <app-brand-button> host too would navigate twice per
  // click and add a Tab stop; only the inner <a> may be a link.
  it('makes only the inner anchors of its buttons focusable links', async () => {
    const harness = await setUp();
    await harness.navigateByUrl('/eneagrama/5');
    const hosts = Array.from(harness.routeNativeElement!.querySelectorAll('app-brand-button'));
    expect(hosts.length).toBe(4);
    for (const host of hosts) {
      expect(host.hasAttribute('tabindex')).toBeFalse();
    }
  });

  it('invites to sign up without a session', async () => {
    const harness = await setUp(null);
    await harness.navigateByUrl('/eneagrama/3');
    const link = harness.routeNativeElement!.querySelector('.cta a')!;
    expect(link.textContent!.trim()).toBe('Empezar gratis');
    expect(link.getAttribute('href')).toBe('/registro');
  });

  it('points to /inicio with a session', async () => {
    const harness = await setUp({ id: 'user-1', displayName: 'Ana' });
    await harness.navigateByUrl('/eneagrama/3');
    const link = harness.routeNativeElement!.querySelector('.cta a')!;
    expect(link.textContent!.trim()).toBe('Ir al test');
    expect(link.getAttribute('href')).toBe('/inicio');
  });
});
