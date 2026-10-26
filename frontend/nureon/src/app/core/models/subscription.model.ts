// Feature 6 — the full plan, paid once through Mercado Pago Checkout Pro for
// a number of days, with no automatic renewal. The backend is the only source
// of all of it: the price shown here is never sent back, and coming back from
// Mercado Pago the frontend only names the payment; whether it bought the
// plan is the backend's answer (backend/docs/api-contract.md).

// GET /api/subscription. The plan's price, currency and days come from the
// backend's configuration, not from this code.
export interface Subscription {
  active: boolean;
  currentPeriodEnd: string | null; // ISO; null without an active paid period
  planPrice: number;
  planCurrency: string;            // 'ARS'
  planDays: number;
}

// POST /api/checkout: where the buyer is sent to pay.
export interface CheckoutSession {
  checkoutUrl: string;
}

export type PaymentStatus = 'approved' | 'pending' | 'rejected';

// POST /api/checkout/confirm: the payment as Mercado Pago reports it to the
// backend, never as the return URL says.
export interface PaymentConfirmation {
  paymentStatus: PaymentStatus;
  currentPeriodEnd: string | null;
}
