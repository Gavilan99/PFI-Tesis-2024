import { CutStatus } from '../models/cut-status.model';

// The fixed, nested cuts the backend serves the test in (Feature 9,
// backend/docs/api-contract.md): items served once each cut is reached.
// CutStatus says which cut an attempt is in and how many items it has
// served, but not where that cut starts; the progress bar counts within the
// cut ("Parte 2 de 3 · 1 de 50"), so the boundaries are needed here too.
export const CUT_ENDS: readonly number[] = [40, 90, 145];

// Accuracy of picking one of the nine types at random: the reference shown
// under each cut's accuracy. The training writes it to
// precision_by_items.json (baseline.chance), but CutStatus doesn't carry it,
// so it's fixed here.
export const CHANCE_ACCURACY = 1 / 9;

// Position of the first item of `cut` (1-based cut number) among everything
// served, 0-based. Cut 1 starts at 0.
export function cutStart(cut: number): number {
  return cut > 1 ? CUT_ENDS[cut - 2] ?? 0 : 0;
}

// Items `cut` adds on top of the previous one.
export function cutSize(cut: number): number {
  return (CUT_ENDS[cut - 1] ?? 0) - cutStart(cut);
}

// The served-items count tells the cut apart: the backend serves exactly
// CUT_ENDS[k] items once cut k + 1 is reached.
export function cutOfServed(served: number): number {
  const index = CUT_ENDS.indexOf(served);
  return index === -1 ? 1 : index + 1;
}

// Accuracy as the product shows it: an integer percentage, or null when
// there's none to show.
export function asPercent(accuracy: number | null | undefined): number | null {
  return typeof accuracy === 'number' && Number.isFinite(accuracy) ? Math.round(accuracy * 100) : null;
}

export function hasNextCut(status: CutStatus): boolean {
  return status.nextCutItems !== null && status.currentCut < status.cutCount;
}
