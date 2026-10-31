import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { FreemiumInfoDialogComponent } from './freemium-info-dialog.component';
import { API_SERVICE, ApiService } from '../../core/services/api.service';

describe('FreemiumInfoDialogComponent', () => {
  function create() {
    const api: Partial<ApiService> = {
      getSubscription: () =>
        of({ active: false, currentPeriodEnd: null, planPrice: 4999, planCurrency: 'ARS', planDays: 30 }),
    };
    TestBed.configureTestingModule({
      imports: [FreemiumInfoDialogComponent],
      providers: [provideRouter([]), { provide: API_SERVICE, useValue: api }],
    });
    const fixture = TestBed.createComponent(FreemiumInfoDialogComponent);
    fixture.detectChanges();
    return fixture;
  }

  afterEach(() => {
    // A spec that fails mid-test must never leave the next one scrolled shut.
    document.body.style.overflow = '';
  });

  it('locks the page behind it while open, and restores scrolling on close', () => {
    const fixture = create();
    expect(document.body.style.overflow).toBe('hidden');

    fixture.destroy();
    expect(document.body.style.overflow).toBe('');
  });
});
