import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { PremiumButtonComponent } from './premium-button.component';
import { API_SERVICE } from '../../../core/services/api.service';
import { ApiError } from '../../../core/services/api-error';

const plan = { active: false, currentPeriodEnd: null, planPrice: 4999, planCurrency: 'ARS', planDays: 30 };

describe('PremiumButtonComponent', () => {
  let api: jasmine.SpyObj<{ getSubscription: () => unknown; startCheckout: () => unknown }>;

  function render() {
    TestBed.configureTestingModule({
      imports: [PremiumButtonComponent],
      providers: [provideRouter([]), { provide: API_SERVICE, useValue: api }],
    });
    const fixture = TestBed.createComponent(PremiumButtonComponent);
    fixture.componentInstance.returnTo = '/test';
    fixture.detectChanges();
    return fixture;
  }

  beforeEach(() => {
    api = jasmine.createSpyObj('ApiService', ['getSubscription', 'startCheckout']);
    api.getSubscription.and.returnValue(of(plan));
    sessionStorage.removeItem('nureon_checkout_return');
  });

  afterEach(() => sessionStorage.removeItem('nureon_checkout_return'));

  it("shows the backend's price, the period and that there is no automatic renewal", () => {
    const text = (render().nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Pasar a premium');
    expect(text).toContain('4.999');
    expect(text).toContain('por 30 días, sin renovación automática');
  });

  it('starts the checkout the backend creates, sending nothing of its own, and remembers where to come back', () => {
    api.startCheckout.and.returnValue(of({ checkoutUrl: '/pago?payment_id=900000001' }));
    const fixture = render();
    const navigate = spyOn(TestBed.inject(Router), 'navigateByUrl').and.resolveTo(true);

    fixture.componentInstance.start();

    expect(api.startCheckout).toHaveBeenCalledWith();
    expect(navigate).toHaveBeenCalledWith('/pago?payment_id=900000001');
    expect(sessionStorage.getItem('nureon_checkout_return')).toBe('/test');
  });

  it("shows the backend's message when the checkout is refused", () => {
    api.startCheckout.and.returnValue(
      throwError(() => new ApiError('Ya tenés el plan completo activo.', 'ALREADY_SUBSCRIBED', 409)),
    );
    const fixture = render();
    fixture.componentInstance.start();
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Ya tenés el plan completo activo.');
  });
});
