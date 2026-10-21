import { TestBed } from '@angular/core/testing';
import { NosotrosComponent } from './nosotros.component';

describe('NosotrosComponent', () => {
  it('lists each person with their role, and nothing left to confirm', () => {
    const fixture = TestBed.createComponent(NosotrosComponent);
    fixture.detectChanges();
    const items = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll('.team__list li'),
      (li) => li.textContent!.replace(/\s+/g, ' ').trim(),
    );

    expect(items).toEqual([
      'Juan Manuel Gavilán: arquitectura, desarrollo del producto e integración del modelo.',
      'Tobías Vodopivec: modelo de negocio, construcción del banco de preguntas, piloto y entrenamiento del modelo.',
      'Ramiro Escalante Leiva: tutor del proyecto.',
    ]);
    expect(fixture.nativeElement.textContent).not.toMatch(/borrador|confirmar|\[/i);
  });
});
