// Evaluados (Feature 20): the people a salud/rrhh account tests in person,
// from its own account — backend-only so far. Not part of ApiService yet;
// http-api.service.ts and mock-api.service.ts implement listSubjects() and
// deleteSubject() directly, ahead of the UI that will use them.
export interface Subject {
  id: string;
  label: string;
  testCount: number;
  lastTestAt: string | null;
  lastTestContext: string | null;
}

// What createTestAttempt's optional second argument carries to administer
// the test to an evaluado instead of the account itself.
export interface SubjectInput {
  label: string;
  context: string | null;
  consentDeclared: boolean;
}
