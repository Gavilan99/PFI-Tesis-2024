import { AnswerOption } from './answer-option.model';

// Client-facing shape of a question — deliberately NOT a 1:1 mirror of the
// `questions` table (PDR — NureonAI Data Model, 2026-08-12).
//
// question_type has four values in the schema; Question Bank v1 only
// populates 'scenario' (163 items, 3 options) and 'multiple_choice' (37
// Likert items, 5 ordered options — the signal is the ordinal position, not
// the option text). 'ordering' and 'text' are schema-valid but out of scope
// until a later item type is authored.
export type QuestionType = 'scenario' | 'multiple_choice' | 'ordering' | 'text';

export interface Question {
  id: string;
  questionType: QuestionType;
  promptText: string;
  displayOrder: number;
  // Not a column on `questions` — the DB relates options via question_id on
  // answer_options. Embedded here because every consumer needs a question
  // together with its options; ApiService.getQuestions() is what assembles it.
  answerOptions: AnswerOption[];

  // grouping_system, version, is_active and created_at all exist on the DB
  // row but are author/versioning metadata the client never acts on — the
  // backend already resolves "the active, current-version question" before
  // responding. grouping_system additionally never displays on screen by
  // design (it's one level removed from group_label, but still part of the
  // instrument's internal bookkeeping, not client-facing data) — see
  // AnswerOption's comment for why group_label specifically must never ship.
}
