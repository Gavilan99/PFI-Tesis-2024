import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, convertToParamMap, provideRouter, Router } from '@angular/router';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { PagoComponent } from './pago.component';
import { API_SERVICE } from '../core/services/api.service';
import { ApiError } from '../core/services/api-error';
import { PaymentConfirmation } from '../core/models/subscription.model';

describe('PagoComponent', () => {
  let api: jasmine.SpyObj<{ confirmPayment: (id: string) => unknown }>;

  function render(query: Record<string, string>, returnTo: string | null = null) {
    if (returnTo) {
      sessionStorage.setItem('nureon_checkout_return', returnTo);
    }
    TestBed.configureTestingModule({
      imports: [PagoComponent, NoopAnimationsModule],
      providers: [
        provideRouter([]),
        { provide: API_SERVICE, useValue: api },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParamMap: convertToParamMap(query) } } },
      ],
    });
    const fixture = TestBed.createComponent(PagoComponent);
    fixture.detectChanges();
    return fixture;
  }

  function text(fixture: { nativeElement: unknown }): string {
    return (fixture.nativeElement as HTMLElement).textContent ?? '';
  }

  function confirming(confirmation: PaymentConfirmation) {
    api.confirmPayment.and.returnValue(of(confirmation));
  }

  beforeEach(() => {
    api = jasmine.createSpyObj('ApiService', ['confirmPayment']);
    sessionStorage.removeItem('nureon_checkout_return');
  });

  afterEach(() => sessionStorage.removeItem('nureon_checkout_return'));

  it('asks the backend about the payment, ignoring the status in the URL', () => {
    confirming({ paymentStatus: 'rejected', currentPeriodEnd: null });
    const fixture = render({ payment_id: '123', status: 'approved' });
    expect(api.confirmPayment).toHaveBeenCalledWith('123');
    expect(text(fixture)).toContain('El pago no se aprobó.');
  });

  it('approved: shows until when and goes back to the same attempt in /test', () => {
    confirming({ paymentStatus: 'approved', currentPeriodEnd: '2026-11-24T12:00:00Z' });
    const fixture = render({ payment_id: '123' }, '/test');
    expect(text(fixture)).toContain('¡Listo! Ya tenés el plan completo.');
    expect(text(fixture)).toContain('noviembre de 2026');
    expect(text(fixture)).toContain('Seguir con el test');
    const navigate = spyOn(TestBed.inject(Router), 'navigateByUrl').and.resolveTo(true);
    fixture.componentInstance.goBack();
    expect(navigate).toHaveBeenCalledWith('/test');
  });

  it('approved from a result: back to that result', () => {
    confirming({ paymentStatus: 'approved', currentPeriodEnd: '2026-11-24T12:00:00Z' });
    const fixture = render({ payment_id: '123' }, '/resultados/attempt-1');
    expect(text(fixture)).toContain('Volver a mi resultado');
    expect(fixture.componentInstance.returnTo).toBe('/resultados/attempt-1');
  });

  it('pending: says so and can ask again', () => {
    confirming({ paymentStatus: 'pending', currentPeriodEnd: null });
    const fixture = render({ payment_id: '123' });
    expect(text(fixture)).toContain('Tu pago está pendiente.');
    fixture.componentInstance.check();
    expect(api.confirmPayment).toHaveBeenCalledTimes(2);
  });

  it('without a payment id: the buyer did not pay, and nothing is asked', () => {
    const fixture = render({});
    expect(api.confirmPayment).not.toHaveBeenCalled();
    expect(text(fixture)).toContain('No completaste el pago.');
  });

  it("someone else's payment shows the backend's message", () => {
    api.confirmPayment.and.returnValue(
      throwError(() => new ApiError('No encontramos ese pago.', 'PAYMENT_NOT_FOUND', 404)),
    );
    expect(text(render({ payment_id: '123' }))).toContain('No encontramos ese pago.');
  });

  it('never goes back to a URL outside the app', () => {
    confirming({ paymentStatus: 'approved', currentPeriodEnd: null });
    const fixture = render({ payment_id: '123' }, 'https://evil.example');
    expect(fixture.componentInstance.returnTo).toBe('/test');
  });
});
