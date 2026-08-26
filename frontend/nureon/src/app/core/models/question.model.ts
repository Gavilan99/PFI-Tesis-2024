import { AnswerOption } from './answer-option.model';

// Mirrors the `questions` table in PDR — NureonAI Data Model (2026-08-12).
// question_type has four values in the schema; Question Bank v1 only
// populates 'scenario' (163 items, 3 options) and 'multiple_choice' (37
// Likert items, 5 ordered options — the signal is the ordinal position, not
// the option text). 'ordering' and 'text' are schema-valid but out of scope
// until a later item type is authored.
export type QuestionType = 'scenario' | 'multiple_choice' | 'ordering' | 'text';

export interface Question {
  id: string;
  // Same caveat as AnswerOption.groupLabel: left as string, not narrowed to
  // a literal union, until the backend's exact wire values are confirmed.
  groupingSystem: string;
  questionType: QuestionType;
  promptText: string;
  version: number;
  isActive: boolean;
  displayOrder: number;
  createdAt: string;
  // Not a column on `questions` — the DB relates options via question_id on
  // answer_options. Embedded here because every consumer needs a question
  // together with its options; ApiService.getQuestions() is what assembles it.
  answerOptions: AnswerOption[];
}
