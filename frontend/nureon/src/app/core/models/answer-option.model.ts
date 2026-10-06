// Client-facing shape of an answer option — deliberately NOT a 1:1 mirror of
// the `answer_options` table (PDR — NureonAI Data Model, 2026-08-12).
//
// group_label is the answer key of the psychometric instrument: it's what
// maps a specific option to a specific eneatype-scoring group. If it ever
// reaches the browser, anyone can read it from devtools and reverse-engineer
// (or game) the test, which invalidates the instrument for professional use.
// It stays in the DB and in the classifier pipeline; the client only ever
// sends back a selected option id, never sees why that id maps to anything.
// See tools/build_question_fixture.py's CONTRACT NOTE — same rule, same
// reasoning, and it's what the Stage 5 fixture actually ships (no
// group_label on any option).
export interface AnswerOption {
  id: string;
  questionId: string;
  optionText: string;
  displayOrder: number;
}
