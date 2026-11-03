// Mirrors the `test_attempts` table in PDR — NureonAI Data Model (2026-08-12).
export type AttemptTier = 'free_reduced' | 'paid_full';
export type AttemptStatus = 'in_progress' | 'completed' | 'abandoned';

export interface TestAttempt {
  id: string;
  // Every attempt belongs to one account (userId, never null). subjectId
  // additionally names the evaluado it was administered to (Feature 20),
  // when a salud/rrhh account tested someone else instead of themselves;
  // the mock only ever populates userId for now.
  userId: string | null;
  subjectId: string | null;
  tier: AttemptTier;
  questionnaireVersion: number;
  status: AttemptStatus;
  startedAt: string;
  completedAt: string | null;
  // The subject's current label (null without one, or once it was
  // deleted) and the free-text context declared for this attempt.
  subjectLabel: string | null;
  subjectContext: string | null;
}
