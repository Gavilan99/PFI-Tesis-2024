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

// Feature 17 (backend) / Feature 18 (this UI): a personalized version of the
// result screen's own four sections (eneatype-content.ts's strengths,
// tensions, growth and stress), generated from the eneatype, descriptionText
// and the account's profile. All four are non-null only when status is
// 'personalized'; every other status means the generic, per-eneatype
// versions in eneatype-content.ts are what gets shown instead.
export interface PersonalizedDescription {
  status: 'not_in_plan' | 'profile_missing' | 'personalized' | 'unavailable';
  strengths: string[] | null;
  tensions: string[] | null;
  growth: string | null;
  stress: string | null;
}
