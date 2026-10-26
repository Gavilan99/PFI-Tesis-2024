import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { EneagramaComponent } from './eneagrama.component';
import { ENEATYPE_CONTENT } from '../resultados/eneatype-content';

describe('EneagramaComponent', () => {
  function render(): HTMLElement {
    TestBed.configureTestingModule({
      imports: [EneagramaComponent],
      providers: [provideRouter([])],
    });
    const fixture = TestBed.createComponent(EneagramaComponent);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('shows the nine types, 1 to 9, as links to their pages', () => {
    const cards = Array.from(render().querySelectorAll<HTMLAnchorElement>('.card-grid > *'));
    expect(cards.length).toBe(9);
    cards.forEach((card, index) => {
      const eneatype = index + 1;
      expect(card.tagName).toBe('A');
      expect(card.getAttribute('href')).toBe(`/eneagrama/${eneatype}`);
      expect(card.textContent).toContain(`Eneatipo ${eneatype} — ${ENEATYPE_CONTENT[eneatype].title}`);
    });
  });

  it('names each triad and its types in the legend', () => {
    const legend = Array.from(render().querySelectorAll('.triad-legend li')).map((li) =>
      li.textContent!.replace(/\s+/g, ' ').trim(),
    );
    expect(legend).toEqual([
      'Instinto: eneatipos 8, 9 y 1',
      'Emoción: eneatipos 2, 3 y 4',
      'Mente: eneatipos 5, 6 y 7',
    ]);
  });
});
