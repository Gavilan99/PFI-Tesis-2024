// Mirrors the `answer_options` table in PDR — NureonAI Data Model (2026-08-12).
export interface AnswerOption {
  id: string;
  questionId: string;
  optionText: string;
  // Group within the question's groupingSystem (e.g. "Cuerpo" within
  // "Centros de Inteligencia") — see the Question Bank v1 doc for the four
  // systems and their groups. Left as string: the exact backend wire values
  // for grouping_system/group_label aren't confirmed yet, so this isn't
  // narrowed to a literal union.
  groupLabel: string;
  displayOrder: number;
}
