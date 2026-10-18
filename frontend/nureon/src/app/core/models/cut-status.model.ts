// Where an attempt stands in the fixed item cuts (40 / 90 / 145)
// and whether it can go on. GET /api/attempts/{id}/cut.
// The accuracy is the estimated eneatype accuracy of a cut, 0-1:
// the number the product shows between cuts. Nothing else of the
// models is exposed.
export interface CutStatus {
  currentCut: number;            // 1-3
  cutCount: number;              // 3
  servedItems: number;           // 40, 90 or 145
  answeredItems: number;
  nextCutItems: number | null;   // items the next cut adds; null on the last
  canContinue: boolean;
  currentCutAccuracy: number;    // 0-1
  nextCutAccuracy: number | null;
  continuedByAttemptId: string | null;
}
