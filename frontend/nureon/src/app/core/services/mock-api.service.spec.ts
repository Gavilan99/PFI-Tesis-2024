import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { MockApiService } from './mock-api.service';
import { ApiError } from './api-error';
import { RegisterInput } from '../models/auth.model';

// MockApiService persists its state here; cleared around each test.
const STATE_KEY = 'nureon_mock_api_state';

const input: RegisterInput = {
  username: 'Persona',
  email: 'persona@example.test',
  password: 'Contraseña-1',
  consentAccepted: true,
};

// build:demo runs on this mock: it has to follow the backend's consent and
// deletion rules, or the demo walks a flow production doesn't have.
describe('MockApiService, consent and deletion (Feature 11)', () => {
  let api: MockApiService;

  beforeEach(() => {
    localStorage.removeItem(STATE_KEY);
    TestBed.configureTestingModule({ providers: [MockApiService, provideHttpClient()] });
    api = TestBed.inject(MockApiService);
  });

  afterEach(() => localStorage.removeItem(STATE_KEY));

  it('rejects a registration without the consent, like the backend', async () => {
    const error = await firstValueFrom(api.register({ ...input, consentAccepted: false })).catch((e) => e);
    expect(error).toEqual(jasmine.any(ApiError));
    expect((error as ApiError).code).toBe('CONSENT_REQUIRED');
    await expectAsync(firstValueFrom(api.login(input))).toBeRejected();
  });

  it('registers with the consent, and after deleting the account the email can no longer log in', async () => {
    const user = await firstValueFrom(api.register(input));
    expect(await firstValueFrom(api.login(input))).toEqual(user);

    await firstValueFrom(api.deleteAccount(user.id));

    const error = await firstValueFrom(api.login(input)).catch((e) => e);
    expect((error as Error).message).toBe('Email o contraseña incorrectos.');
    // The email is free again.
    expect((await firstValueFrom(api.register(input))).email).toBe(input.email);
  });
});

// build:demo walks the payment on this mock too: approved on the spot, like
// the backend's local gateway, and only for the account that started it.
describe('MockApiService, payments (Feature 6)', () => {
  let api: MockApiService;

  beforeEach(() => {
    localStorage.removeItem(STATE_KEY);
    TestBed.configureTestingModule({ providers: [MockApiService, provideHttpClient()] });
    api = TestBed.inject(MockApiService);
  });

  afterEach(() => localStorage.removeItem(STATE_KEY));

  function paymentIdOf(checkoutUrl: string): string {
    return new URL(checkoutUrl, 'http://localhost').searchParams.get('payment_id')!;
  }

  it('starts without the plan, pays, and then has it', async () => {
    await firstValueFrom(api.register(input));
    expect((await firstValueFrom(api.getSubscription())).active).toBeFalse();

    const { checkoutUrl } = await firstValueFrom(api.startCheckout());
    const confirmation = await firstValueFrom(api.confirmPayment(paymentIdOf(checkoutUrl)));

    expect(confirmation.paymentStatus).toBe('approved');
    expect((await firstValueFrom(api.getSubscription())).active).toBeTrue();
    const again = await firstValueFrom(api.startCheckout()).catch((e) => e);
    expect((again as ApiError).code).toBe('ALREADY_SUBSCRIBED');
  });

  it("answers someone else's payment like one that does not exist", async () => {
    await firstValueFrom(api.register(input));
    const { checkoutUrl } = await firstValueFrom(api.startCheckout());
    await firstValueFrom(api.register({ ...input, email: 'otra@example.test' }));

    const error = await firstValueFrom(api.confirmPayment(paymentIdOf(checkoutUrl))).catch((e) => e);
    expect((error as ApiError).code).toBe('PAYMENT_NOT_FOUND');
  });
});
