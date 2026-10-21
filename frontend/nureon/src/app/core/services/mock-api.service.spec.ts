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
