// Evaluados (Feature 20 backend / Feature 21 UI): the people a salud/rrhh
// account tests in person, from its own account.
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
