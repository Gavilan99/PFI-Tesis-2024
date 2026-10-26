// Every text of paying for the full plan (Feature 6): the "Pasar a premium"
// button and the /pago screen the buyer lands on back from Mercado Pago.
// Provisional wording, like CUT_COPY — change it here and nowhere else.
export const CHECKOUT_COPY = {
  goPremium: 'Pasar a premium',
  // The price comes from the backend's configuration (GET /api/subscription).
  planPrice: (price: number, currency: string, days: number) =>
    `${formatPrice(price, currency)} por ${days} días, sin renovación automática. Pagás con Mercado Pago.`,
  startError: 'No pudimos iniciar el pago. Probá de nuevo en unos minutos.',

  // /pago.
  checking: 'Estamos confirmando tu pago con Mercado Pago…',
  approvedTitle: '¡Listo! Ya tenés el plan completo.',
  approvedBody: (until: string) => `Lo podés usar hasta el ${until}.`,
  pendingTitle: 'Tu pago está pendiente.',
  pendingBody:
    'Mercado Pago todavía no lo aprobó. Cuando lo apruebe, el plan completo se activa solo: ' +
    'podés volver a consultar en un rato.',
  rejectedTitle: 'El pago no se aprobó.',
  rejectedBody: 'No se te cobró nada. Podés probar de nuevo con otro medio de pago.',
  abandonedTitle: 'No completaste el pago.',
  abandonedBody: 'No se te cobró nada. Cuando quieras, podés pasar a premium desde el test o tu resultado.',
  checkError: 'No pudimos confirmar tu pago. Probá de nuevo en unos minutos.',
  continueTest: 'Seguir con el test',
  backToResult: 'Volver a mi resultado',
  refresh: 'Volver a consultar',
  tryAgain: 'Probar de nuevo',
  home: 'Ir al inicio',
} as const;

export function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat('es-AR', { style: 'currency', currency }).format(price);
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('es-AR', { day: 'numeric', month: 'long', year: 'numeric' }).format(
    new Date(iso),
  );
}
