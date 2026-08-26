// Mirrors the `responses` table in PDR — NureonAI Data Model (2026-08-12).
// Named TestResponse, not Response, to avoid shadowing the global fetch
// Response type that every .ts file has in scope via the DOM lib.
export interface TestResponse {
  id: string;
  testAttemptId: string;
  questionId: string;
  selectedOptionId: string | null;
  freeTextResponse: string | null;
  // jsonb on the DB side; shape is undefined until an 'ordering' question
  // ships (Question Bank v1 doesn't use that type), so left unopinionated.
  orderingResponse: unknown | null;
  answeredAt: string;
}

// What a caller provides when submitting a response — the fields the
// backend generates (id, testAttemptId, answeredAt) are excluded.
export type NewResponseInput = Pick<
  TestResponse,
  'questionId' | 'selectedOptionId' | 'freeTextResponse' | 'orderingResponse'
>;
