// Mirrors the `results` table in PDR — NureonAI Data Model (2026-08-12).
// `confidence_margin` and the 4 classifiers' raw probabilities exist on the
// backend but are internal-only per the PDR ("never exposed to end users")
// — deliberately not part of this frontend-facing contract.
export interface Result {
  id: string;
  testAttemptId: string;
  eneatype: number; // 1-9
  descriptionText: string;
  generatedAt: string;
}
