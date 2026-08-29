// Mirrors the subset of the `users` table (PDR — NureonAI Data Model) that's
// actually populated at registration time. account_type, age_range, gender,
// country and profession_context are profile fields collected later (RF07,
// Stage 7) — not modeled here yet, to avoid inventing defaults for them.
export interface User {
  id: string;
  displayName: string;
  email: string;
}
