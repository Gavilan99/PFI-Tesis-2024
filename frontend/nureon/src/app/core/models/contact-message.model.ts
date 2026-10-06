// No `contact_messages` table exists in the PDR data model yet — this is a
// mock-only convenience for the `/contacto` form (Stage 10) so it has
// somewhere real to submit to instead of being purely decorative. Follows
// SubmitFeedbackInput's shape: plain fields, fire-and-forget from the
// client's point of view.
export interface SubmitContactMessageInput {
  name: string;
  email: string;
  message: string;
}
