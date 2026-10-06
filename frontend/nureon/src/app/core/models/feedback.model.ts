// Mirrors the `feedback` table (PDR — NureonAI Data Model). test_attempt_id
// and user_id are both nullable on the DB side; in this app feedback always
// comes from a logged-in user, so user_id is implicit server-side (never
// sent from the client, same reasoning as elsewhere: the client sends what
// it directly knows, not identifiers the backend already has from the
// session) — testAttemptId is the only real variation, since feedback can be
// general (from the profile) or tied to the test just finished.
export interface SubmitFeedbackInput {
  testAttemptId: string | null;
  rating: number; // 1-5
  comment: string | null;
}
