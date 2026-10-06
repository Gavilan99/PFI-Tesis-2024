// Mirrors the `test_attempts` table in PDR — NureonAI Data Model (2026-08-12).
export type AttemptTier = 'free_reduced' | 'paid_full';
export type AttemptStatus = 'in_progress' | 'completed' | 'abandoned';

export interface TestAttempt {
  id: string;
  // XOR with subjectId at the DB level (CHECK constraint) — an attempt
  // belongs to a self-testing user or a professional-administered subject,
  // never both, never neither. Professional/subject accounts are Stage 4+
  // scope; the mock only ever populates userId for now.
  userId: string | null;
  subjectId: string | null;
  tier: AttemptTier;
  questionnaireVersion: number;
  status: AttemptStatus;
  startedAt: string;
  completedAt: string | null;
}
