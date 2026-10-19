// The Error every ApiService method rejects with. `message` is Spanish and
// meant to be shown as is (the registro and ingreso forms already do); `code`
// and `status` are there for whoever needs to tell errors apart.
export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Continuing to a cut the account's tier doesn't include (402). The screens
// that continue show the plans text for it instead of a generic error.
export const PAID_TIER_REQUIRED = 'PAID_TIER_REQUIRED';

export function isPaidTierRequired(error: unknown): boolean {
  return error instanceof ApiError && error.code === PAID_TIER_REQUIRED;
}
