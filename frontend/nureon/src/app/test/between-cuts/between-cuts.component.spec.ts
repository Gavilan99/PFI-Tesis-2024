import { TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { BetweenCutsComponent } from './between-cuts.component';
import { API_SERVICE } from '../../core/services/api.service';
import { CutStatus } from '../../core/models/cut-status.model';

const status: CutStatus = {
  currentCut: 1,
  cutCount: 3,
  servedItems: 40,
  answeredItems: 40,
  nextCutItems: 50,
  canContinue: true,
  currentCutAccuracy: 0.17,
  nextCutAccuracy: 0.18,
  continuedByAttemptId: null,
};

describe('BetweenCutsComponent', () => {
  function render(overrides: Partial<CutStatus> = {}): string {
    TestBed.configureTestingModule({
      imports: [BetweenCutsComponent, NoopAnimationsModule],
      providers: [{ provide: API_SERVICE, useValue: {} }],
    });
    const fixture = TestBed.createComponent(BetweenCutsComponent);
    fixture.componentInstance.status = { ...status, ...overrides };
    fixture.detectChanges();
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  it('shows the chance reference under the accuracy of the cut', () => {
    const text = render();
    expect(text).toContain('aproximadamente 17 % de los casos');
    expect(text).toContain(
      'Como referencia, elegir un tipo al azar acertaría en el 11 % de los casos.',
    );
  });
});
