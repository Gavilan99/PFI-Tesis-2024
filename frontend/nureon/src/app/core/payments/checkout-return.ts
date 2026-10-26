// Where to go after paying: the screen the buyer left for Mercado Pago (/test,
// or /resultados/:id). Navigation only — it never says anything about the
// tier, which only the backend knows. sessionStorage, so it lives as long as
// the tab; it can be unavailable (private mode, blocked storage), and then
// /pago falls back to /test and /inicio.
const STORAGE_KEY = 'nureon_checkout_return';

export function saveCheckoutReturn(path: string): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, path);
  } catch {
    // Without storage the fallback applies.
  }
}

export function readCheckoutReturn(): string | null {
  try {
    const path = sessionStorage.getItem(STORAGE_KEY);
    // Only a path of this app: never a URL somewhere else.
    return path && /^\/(test|resultados(\/[\w-]+)?)$/.test(path) ? path : null;
  } catch {
    return null;
  }
}
