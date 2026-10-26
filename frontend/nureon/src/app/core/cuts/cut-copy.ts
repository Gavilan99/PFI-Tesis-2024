// Every text of the cuts, in one place: the screen between cuts (/test) and
// the "afinar tu resultado" block of /resultados. Provisional wording, still
// to be confirmed with Tobi — change it here and nowhere else.
export const CUT_COPY = {
  progressPrefix: (cut: number, cutCount: number) => `Parte ${cut} de ${cutCount} · `,

  // Shown on the first question of the test. Added after the pilot, where
  // participants hesitated between answering as they are or as they would
  // like to be.
  instruction: 'Respondé según cómo sos, no según cómo te gustaría ser. No pienses en el test como una evaluación.',

  // Screen between cuts.
  finishedPart: (cut: number, cutCount: number) => `Terminaste la parte ${cut} de ${cutCount}.`,
  currentAccuracy: (answered: number, percent: number) =>
    `Con las ${answered} preguntas que respondiste, el resultado coincide con la tipificación de un especialista en aproximadamente ${percent}\u00a0% de los casos.`,
  chanceReference: (percent: number) =>
    `Como referencia, elegir un tipo al azar acertaría en el ${percent} % de los casos.`,
  nextAccuracy: (more: number, percent: number) =>
    `Si respondés ${more} preguntas más, esa coincidencia estimada pasa a ser de ${percent}\u00a0%.`,
  seeResult: 'Ver mi resultado',
  continueWith: (more: number) => `Seguir con ${more} preguntas más`,

  // Not premium: the plans text. The accuracy part is left out when the
  // next cut has no accuracy to show.
  plansCanContinue: (more: number, percent: number | null) =>
    percent === null
      ? `Podés seguir con ${more} preguntas más.`
      : `Podés seguir con ${more} preguntas más y llevar esa coincidencia estimada a ${percent}\u00a0%.`,
  plansIncludedParts: (fromPart: number, cutCount: number) => {
    const parts = Array.from({ length: cutCount - fromPart + 1 }, (_, i) => fromPart + i);
    return parts.length === 1
      ? `La parte ${parts[0]} está incluida en el plan premium.`
      : `Las partes ${parts.slice(0, -1).join(', ')} y ${parts[parts.length - 1]} están incluidas en el plan premium.`;
  },
  // "Pasar a premium" and the price: core/payments/checkout-copy.ts (Feature 6).

  // /resultados.
  refineTitle: '¿Querés afinar tu resultado?',
  refineBody: (more: number) =>
    `Respondé ${more} preguntas más; las que ya respondiste quedan guardadas.`,
  continueFromResult: 'Seguir',

  // Errors that aren't the paid tier.
  continueError: 'No pudimos seguir con el test.',
} as const;
