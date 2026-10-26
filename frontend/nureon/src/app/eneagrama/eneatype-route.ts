import { inject } from '@angular/core';
import { CanActivateFn, ResolveFn, Router } from '@angular/router';
import { eneatypeLabel } from '../resultados/eneatype-content';

// /eneagrama/:tipo takes exactly one digit, 1 to 9. Anything else ("0",
// "10", "abc", "01") isn't a type, so it goes back to /eneagrama rather than
// to the 404: whoever typed it was looking for a type.
export function parseEneatype(value: string | null): number | null {
  return value !== null && /^[1-9]$/.test(value) ? Number(value) : null;
}

export const eneatypeGuard: CanActivateFn = (route) =>
  parseEneatype(route.paramMap.get('tipo')) !== null || inject(Router).createUrlTree(['/eneagrama']);

// Resolved into data.title, which PageTitleService turns into the <title>.
// Only runs after eneatypeGuard, so the param is always valid here.
export const eneatypeTitleResolver: ResolveFn<string> = (route) =>
  eneatypeLabel(parseEneatype(route.paramMap.get('tipo'))!);
