import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { FooterComponent } from './footer.component';

describe('FooterComponent', () => {
  it('links the privacy policy and the terms', () => {
    TestBed.configureTestingModule({ imports: [FooterComponent], providers: [provideRouter([])] });
    const fixture = TestBed.createComponent(FooterComponent);
    fixture.detectChanges();

    const links = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('a')).map((a) => [
      a.textContent?.trim(),
      a.getAttribute('href'),
    ]);
    expect(links).toEqual([
      ['Política de privacidad', '/privacidad'],
      ['Términos y condiciones', '/terminos'],
    ]);
  });
});
