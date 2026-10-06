import { AccountType } from '../core/models/user.model';

// PROVISIONAL — adaptado y traducido de src/assets/data/type_*.txt (en
// inglés, con formato inconsistente entre archivos: type_1/2 usan un
// esquema, type_3-9 otro). No es la redacción final del contenido de
// resultados — placeholder hasta que se escriba el texto real en español.
// isPlaceholder existe para que la UI lo marque explícitamente en pantalla.
export interface EneatypeContent {
  title: string;
  summary: string;
  coreMotivation: string;
  strengths: string[];
  tensions: string[];
  growth: string;
  stress: string;
  isPlaceholder: boolean;
}

export const ENEATYPE_CONTENT: Record<number, EneatypeContent> = {
  1: {
    title: 'El Reformador',
    summary: 'Principista, con propósito, autocontrolado y perfeccionista.',
    coreMotivation:
      'Buscás tener razón, mejorar todo lo que te rodea y evitar la culpa o el error.',
    strengths: [
      'Busca la mejora constante',
      'Estándares altos',
      'Fuerte sentido ético',
      'Organizado y eficiente',
      'Consciente y racional',
    ],
    tensions: [
      'Puede ser crítico consigo mismo y con otros',
      'Tiende al resentimiento cuando las cosas no cumplen sus expectativas',
      'Le cuesta relajarse y aceptar la imperfección',
      'Tendencia a la impaciencia',
    ],
    growth:
      'En crecimiento, te volvés más aceptador, paciente y espontáneo — abrazás las imperfecciones de la vida con más autocompasión.',
    stress:
      'Bajo estrés, podés volverte más controlador y rígido, sintiéndote abrumado por la frustración y excesivamente crítico.',
    isPlaceholder: true,
  },
  2: {
    title: 'El Ayudador',
    summary: 'Cálido, cercano, generoso y complaciente con los demás.',
    coreMotivation:
      'Necesitás sentirte querido y necesitado, y por eso das mucho de vos para ayudar a los demás.',
    strengths: [
      'Empático y compasivo',
      'Fuerte deseo de ayudar',
      'Generoso y protector',
      'Bueno para construir vínculos',
      'Intuitivo sobre las necesidades ajenas',
    ],
    tensions: [
      'Puede volverse posesivo y dependiente',
      'Le cuesta reconocer sus propias necesidades',
      'Tiende a la complacencia y a buscar aprobación',
      'Puede sentirse no valorado cuando su esfuerzo pasa desapercibido',
    ],
    growth:
      'En crecimiento, te volvés más autónomo y capaz de cuidarte a vos mismo — aprendés a poner límites y priorizar tus propias necesidades.',
    stress:
      'Bajo estrés, podés volverte invasivo o manipulador, sintiéndote herido cuando tu ayuda no se ve reciprocada.',
    isPlaceholder: true,
  },
  3: {
    title: 'El Triunfador',
    summary: 'Seguro de sí mismo, ambicioso, orientado a resultados y consciente de su imagen.',
    coreMotivation:
      'Necesitás sentirte valioso a través de tus logros y ser admirado por lo que conseguís.',
    strengths: [
      'Seguro y carismático',
      'Ambicioso y competente',
      'Orientado a metas y al éxito',
      'Adaptable en distintos entornos',
      'Eficiente y práctico',
    ],
    tensions: [
      'Puede volverse excesivamente competitivo',
      'Puede descuidar sus emociones por enfocarse en producir',
      'Tendencia a mostrar una imagen antes que su ser auténtico',
      'Puede ser impaciente con quienes ve menos motivados',
    ],
    growth:
      'En crecimiento, desarrollás autenticidad y reconocés que tu valor no depende del éxito externo — te permitís conectar con emociones más profundas.',
    stress:
      'Bajo estrés, podés sentir que fallaste o que no estás a la altura de una imagen ideal, y descuidar tus necesidades emocionales.',
    isPlaceholder: true,
  },
  4: {
    title: 'El Individualista',
    summary: 'Creativo, expresivo, introspectivo y emocionalmente honesto.',
    coreMotivation:
      'Buscás encontrar tu identidad única y darle un sentido personal y auténtico a tu vida.',
    strengths: [
      'Creativo y expresivo',
      'Emocionalmente honesto y auténtico',
      'Introspectivo y con autoconciencia',
      'Sensible y empático',
      'Capaz de apreciar la belleza y la profundidad',
    ],
    tensions: [
      'Propenso a cambios de humor y melancolía',
      'Puede volverse retraído y absorto en sí mismo',
      'Tiende a compararse con otros y sentirse en falta',
      'Puede quedarse instalado en sus emociones sin resolverlas',
    ],
    growth:
      'En crecimiento, aprendés a aceptarte y valorarte tal cual sos, sin necesidad de ser distinto o especial.',
    stress:
      'Bajo estrés, podés sentirte incomprendido o desconectado, con episodios de melancolía o aislamiento.',
    isPlaceholder: true,
  },
  5: {
    title: 'El Investigador',
    summary: 'Analítico, independiente, perceptivo y reservado.',
    coreMotivation:
      'Necesitás entender el mundo a fondo y conservar tu energía y tu espacio propio.',
    strengths: [
      'Analítico y perspicaz',
      'Independiente y autosuficiente',
      'Pensador objetivo',
      'Mantiene la calma en situaciones difíciles',
      'Buen resolutor de problemas',
    ],
    tensions: [
      'Puede volverse emocionalmente distante',
      'Le cuesta expresar sentimientos o necesidades',
      'Tiende a intelectualizar en vez de sentir',
      'Puede aislarse de los demás',
      'Le cuesta confiar cuestiones personales',
    ],
    growth:
      'En crecimiento, te animás a compartir tus emociones y a confiar más en los demás, balanceando lo intelectual con lo emocional.',
    stress:
      'Bajo estrés, podés sentirte abrumado por la interacción social y retraerte, intelectualizando los problemas para evitar sentirlos.',
    isPlaceholder: true,
  },
  6: {
    title: 'El Leal',
    summary: 'Comprometido, responsable, cooperativo y alerta a los riesgos.',
    coreMotivation: 'Buscás seguridad y apoyo, y anticipás problemas para sentirte preparado.',
    strengths: [
      'Leal y comprometido',
      'Responsable y confiable',
      'Buen resolutor práctico de problemas',
      'Valiente frente a los desafíos',
      'Muy cooperativo',
    ],
    tensions: [
      'Propenso a la ansiedad',
      'Puede volverse suspicaz',
      'Le cuesta decidir y confiar en sí mismo',
      'Puede depender de otros para sentirse seguro',
      'Tiende a anticipar el peor escenario',
    ],
    growth:
      'En crecimiento, aprendés a confiar en vos mismo y en tu intuición, decidiendo sin necesitar tanta validación externa.',
    stress:
      'Bajo estrés, podés sentirte abrumado por la ansiedad y paralizado por la indecisión.',
    isPlaceholder: true,
  },
  7: {
    title: 'El Entusiasta',
    summary: 'Optimista, espontáneo, curioso y siempre buscando la próxima experiencia.',
    coreMotivation:
      'Buscás evitar el dolor y el aburrimiento persiguiendo posibilidades y experiencias nuevas.',
    strengths: [
      'Entusiasta y optimista',
      'Espontáneo y aventurero',
      'Rápido para encontrar soluciones',
      'Muy curioso',
      'Adaptable en situaciones diversas',
    ],
    tensions: [
      'Le cuesta mantener el foco y el compromiso',
      'Puede evitar emociones o situaciones difíciles',
      'Propenso a la impulsividad',
      'Inquieto, siempre busca lo nuevo',
      'Puede dispersarse',
    ],
    growth:
      'En crecimiento, aprendés a quedarte con las emociones difíciles en vez de evitarlas, y a sostener el compromiso en el tiempo.',
    stress:
      'Bajo estrés, podés sentirte atrapado por los compromisos y frustrado cuando la realidad no coincide con lo idealizado.',
    isPlaceholder: true,
  },
  8: {
    title: 'El Desafiador',
    summary: 'Seguro, decidido, protector y con fuerte liderazgo.',
    coreMotivation:
      'Necesitás protegerte a vos mismo y a los tuyos, evitando quedar en una posición vulnerable.',
    strengths: [
      'Seguro y decidido',
      'Protector y con recursos',
      'Fuertes cualidades de liderazgo',
      'Asertivo y orientado a la acción',
      'Capaz de defenderse y defender a otros',
    ],
    tensions: [
      'Puede volverse confrontativo o dominante',
      'Le cuesta mostrar vulnerabilidad',
      'Puede resistirse a depender de otros',
      'Propenso a la intensidad excesiva',
      'Impaciente con la debilidad ajena',
    ],
    growth:
      'En crecimiento, te abrís a la vulnerabilidad y a la sensibilidad emocional, soltando la necesidad de controlar todo.',
    stress:
      'Bajo estrés, podés reaccionar con enojo o confrontación al sentirte amenazado o fuera de control.',
    isPlaceholder: true,
  },
  9: {
    title: 'El Pacificador',
    summary: 'Tranquilo, conciliador, empático y capaz de ver todas las perspectivas.',
    coreMotivation:
      'Buscás mantener la paz interior y evitar el conflicto para sostener la armonía.',
    strengths: [
      'Calmo y en paz',
      'No juzga y acepta a los demás',
      'Apoyador y empático',
      'Ve múltiples perspectivas',
      'Armonioso y paciente',
    ],
    tensions: [
      'Tiende a evitar el conflicto a toda costa',
      'Le cuesta afirmarse o expresar sus necesidades',
      'Puede volverse pasivo o desconectado',
      'Propenso a la procrastinación',
      'Le cuesta decidir o priorizarse',
    ],
    growth:
      'En crecimiento, aprendés a afirmarte y a expresar tus opiniones, abrazando el conflicto como una oportunidad.',
    stress:
      'Bajo estrés, podés sentirte abrumado por la confrontación y desconectarte de vos mismo y de tus metas.',
    isPlaceholder: true,
  },
};

// RF09/RF10 encuadre slot: the result is identical for every persona, only
// the framing sentence around it changes. Keyed by the user's own
// AccountType (Stage 7) — no separate "encuadre" concept, it's literally
// which persona the account is. Only 'individual' has real copy —
// 'salud'/'rrhh' are null on purpose (unwritten content, not missing wiring).
// The component falls back to 'individual' when the specific framing is
// null, so finishing this later is content work, not structural work.
export interface EneatypeFraming {
  intro: string | null;
}

export const FRAMING_TEXT: Record<AccountType, EneatypeFraming> = {
  individual: {
    intro:
      'Este es tu perfil de motivación: te ayuda a entender qué te mueve, no solo cómo actuás.',
  },
  salud: { intro: null },
  rrhh: { intro: null },
};
