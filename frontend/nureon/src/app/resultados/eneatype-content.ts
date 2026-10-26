import { AccountType } from '../core/models/user.model';

// Everything NureonAI says about each eneatype, in one place: the type names
// (the usual ones in the eneagrama literature), the triad and color, the
// result screen's text, and the short public page at /eneagrama/:tipo. The
// wording is our own: a guide to personality centred on motivation, not a
// diagnosis. `summary` is also the result's descriptionText: the backend
// keeps a copy in app/services/result_descriptions.py, and
// backend/tests/test_result_descriptions.py fails if the two drift apart —
// it reads `title` and `summary` as the first two fields of each entry, so
// they stay there.
//
// `page` is public and free; everything from `summary` to `stress` is the
// result. The page must never repeat the result's text, or it would give
// away what the full profile unlocks (eneatype-content.spec.ts checks it).
export type Triad = 'instinct' | 'emotion' | 'mind';

export interface EneatypePage {
  strengths: string[];
  weaknesses: string[];
  growth: string[];
  tensions: string[];
}

export interface EneatypeContent {
  title: string;
  summary: string;
  coreMotivation: string;
  strengths: string[];
  tensions: string[];
  growth: string;
  stress: string;
  triad: Triad;
  // Custom property name from styles/_tokens.scss, read as var(color).
  color: string;
  page: EneatypePage;
}

export interface TriadInfo {
  id: Triad;
  label: string;
  name: string;
  eneatypes: number[];
}

// The three centers of intelligence, in the eneagrama's usual order.
export const TRIADS: TriadInfo[] = [
  { id: 'instinct', label: 'Instinto', name: 'Tríada del instinto', eneatypes: [8, 9, 1] },
  { id: 'emotion', label: 'Emoción', name: 'Tríada de la emoción', eneatypes: [2, 3, 4] },
  { id: 'mind', label: 'Mente', name: 'Tríada de la mente', eneatypes: [5, 6, 7] },
];

export const ENEATYPE_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9];

// "Eneatipo 1 — El Reformador": the cards, the page heading and its <title>.
export function eneatypeLabel(eneatype: number): string {
  return `Eneatipo ${eneatype} — ${ENEATYPE_CONTENT[eneatype].title}`;
}

export const ENEATYPE_CONTENT: Record<number, EneatypeContent> = {
  1: {
    title: 'El Reformador',
    summary: 'Íntegro, exigente, ordenado y comprometido con hacer las cosas bien.',
    coreMotivation:
      'Te mueve hacer lo correcto: sentir que actuás con integridad y que lo que pasa por tus manos queda mejor de lo que estaba.',
    strengths: [
      'Tiene claro qué es justo y lo sostiene',
      'Cuida los detalles y la calidad',
      'Es coherente entre lo que dice y lo que hace',
      'Pone orden donde hace falta',
      'Asume la responsabilidad que le toca',
    ],
    tensions: [
      'Puede ser muy duro consigo mismo y con los demás',
      'Le cuesta dar algo por terminado si no quedó impecable',
      'Se guarda el enojo cuando algo le parece injusto',
      'Puede ver un único modo correcto de hacer las cosas',
    ],
    growth:
      'En crecimiento, te das permiso para disfrutar y para equivocarte, y tu exigencia se vuelve más amable con vos y con los demás.',
    stress:
      'Bajo estrés, podés volverte más rígido y crítico, y sentir que todo depende de que vos lo corrijas.',
    triad: 'instinct',
    color: '--nureon-type-1',
    page: {
      strengths: [
        'Se guía por principios firmes, también cuando nadie lo mira.',
        'Trabaja con método y no deja cabos sueltos.',
        'Detecta enseguida qué se puede mejorar.',
        'Es alguien en cuya palabra se puede confiar.',
      ],
      weaknesses: [
        'Su tono puede sonar a reproche aunque no sea su intención.',
        'Le cuesta delegar por miedo a que no quede bien hecho.',
        'Posterga el descanso y el disfrute hasta haber cumplido.',
      ],
      growth: [
        'Se vuelve más espontáneo y se permite disfrutar sin culpa.',
        'Acepta que hay más de una forma válida de resolver algo.',
        'Pone su sentido de lo justo al servicio de los demás, con más humor y menos rigidez.',
      ],
      tensions: [
        'Se siente incomprendido y se repliega en su malestar.',
        'El enojo que no dijo se vuelve desánimo.',
        'Se compara con un ideal que nunca alcanza.',
      ],
    },
  },
  2: {
    title: 'El Ayudador',
    summary: 'Atento, afectuoso, generoso y pendiente de lo que necesitan los demás.',
    coreMotivation:
      'Te mueve sentirte querido e importante para las personas, y lo buscás estando cerca y ofreciendo tu ayuda.',
    strengths: [
      'Percibe rápido cómo está el otro',
      'Se ofrece sin que se lo pidan',
      'Crea vínculos cálidos y cercanos',
      'Hace que los demás se sientan acompañados',
      'Es generoso con su tiempo y su energía',
    ],
    tensions: [
      'Puede dejar sus propias necesidades para después',
      'Le cuesta pedir ayuda o decir que no',
      'Puede esperar reconocimiento a cambio de lo que da',
      'Se siente dolido cuando su esfuerzo no se nota',
    ],
    growth:
      'En crecimiento, te cuidás con la misma atención que les das a los demás, y ayudás sin esperar nada a cambio.',
    stress:
      'Bajo estrés, podés insistir con tu ayuda aunque no te la pidan y sentir que nadie valora lo que hacés.',
    triad: 'emotion',
    color: '--nureon-type-2',
    page: {
      strengths: [
        'Registra los detalles que hacen sentir bien a cada persona.',
        'Está presente cuando alguien atraviesa un mal momento.',
        'Genera confianza con facilidad.',
        'Logra que un grupo se sienta más unido.',
      ],
      weaknesses: [
        'Puede meterse en asuntos ajenos con la mejor intención.',
        'Se ocupa tanto de los demás que se olvida de sí.',
        'Su ayuda puede venir con expectativas que no dice en voz alta.',
        'Puede tomar como un rechazo que alguien no acepte su ayuda.',
      ],
      growth: [
        'Se conecta con lo que siente y con lo que quiere para sí.',
        'Da porque quiere, no para ganarse un lugar.',
        'Se anima a mostrar su lado más creativo y personal.',
      ],
      tensions: [
        'Se vuelve demandante y reclama lo que siente que le deben.',
        'Su generosidad se transforma en enojo o en control.',
        'Le cuesta aceptar un no como respuesta.',
      ],
    },
  },
  3: {
    title: 'El Triunfador',
    summary: 'Enérgico, eficaz, orientado a metas y atento a la impresión que causa.',
    coreMotivation:
      'Te mueve sentir que valés por lo que lográs, y por eso ponés mucha energía en avanzar y en que tus logros se vean.',
    strengths: [
      'Se fija objetivos y los cumple',
      'Contagia empuje a su equipo',
      'Se adapta rápido a lo que pide cada situación',
      'Sabe presentar bien sus ideas',
      'Prioriza lo que da resultados',
    ],
    tensions: [
      'Puede medir su valor sólo por sus logros',
      'Deja de lado lo que siente para no frenar',
      'Tiende a mostrar la versión de sí que más conviene',
      'Le cuesta bajar el ritmo',
    ],
    growth:
      'En crecimiento, te mostrás como sos y no sólo por lo que rendís, y descubrís que tu valor no depende de cada logro.',
    stress:
      'Bajo estrés, podés exigirte cada vez más para no sentir que fallaste, aunque eso te aleje de lo que sentís.',
    triad: 'emotion',
    color: '--nureon-type-3',
    page: {
      strengths: [
        'Convierte una idea en un plan concreto y lo lleva adelante.',
        'Trabaja con foco y aprovecha bien el tiempo.',
        'Motiva a otros con su ejemplo.',
        'Se desenvuelve con soltura frente a otras personas.',
      ],
      weaknesses: [
        'Puede cuidar tanto su imagen que pierde de vista cómo se siente.',
        'Vive la comparación con otros como una competencia.',
        'Le cuesta tolerar el fracaso, propio o del equipo.',
        'Llena la agenda hasta no dejar lugar para el descanso.',
      ],
      growth: [
        'Se compromete con proyectos compartidos, no sólo con los propios.',
        'Se muestra auténtico, con dudas y todo.',
        'Valora los vínculos tanto como los resultados.',
      ],
      tensions: [
        'Se desconecta y pierde su impulso habitual.',
        'Posterga decisiones y se distrae con tareas que no importan.',
        'Se apaga en lugar de pedir ayuda.',
      ],
    },
  },
  4: {
    title: 'El Individualista',
    summary: 'Sensible, creativo, profundo y fiel a su propia manera de ver las cosas.',
    coreMotivation:
      'Te mueve descubrir quién sos de verdad y que tu vida tenga un sentido propio, que te represente.',
    strengths: [
      'Pone en palabras lo que otros no saben decir',
      'Tiene una mirada original',
      'Se conoce bien por dentro',
      'Acompaña bien a otros en momentos difíciles',
      'Encuentra belleza y sentido en lo cotidiano',
    ],
    tensions: [
      'Su estado de ánimo puede cambiar mucho',
      'Puede sentir que le falta algo que otros tienen',
      'Tiende a encerrarse en lo que siente',
      'Le cuesta valorar lo que ya tiene',
    ],
    growth:
      'En crecimiento, dejás de buscar lo que te falta y te sentís a gusto con quien ya sos, y tu creatividad se vuelca hacia afuera.',
    stress:
      'Bajo estrés, podés sentir que nadie te entiende y replegarte en tu mundo interior.',
    triad: 'emotion',
    color: '--nureon-type-4',
    page: {
      strengths: [
        'Expresa las emociones con honestidad y profundidad.',
        'Le imprime un estilo propio a lo que hace.',
        'No le teme a las conversaciones sobre lo que duele.',
        'Valora la autenticidad, en sí y en los demás.',
      ],
      weaknesses: [
        'Puede quedarse dándole vueltas a una emoción durante mucho tiempo.',
        'Se siente distinto al resto, a veces hasta aislarse.',
        'Tiende a idealizar el pasado o lo lejano y a desvalorizar el presente.',
        'Se toma las críticas de manera muy personal.',
      ],
      growth: [
        'Pasa de sentir a hacer: le da forma concreta a lo que imagina.',
        'Gana constancia y disciplina sin perder sensibilidad.',
        'Se apoya en principios claros y no sólo en cómo se siente ese día.',
      ],
      tensions: [
        'Busca con ansiedad la atención y el afecto de los demás.',
        'Puede depender de la aprobación ajena.',
        'Se desvive por agradar y después le pasa factura.',
      ],
    },
  },
  5: {
    title: 'El Investigador',
    summary: 'Curioso, observador, autónomo y de pocas palabras.',
    coreMotivation:
      'Te mueve comprender cómo funcionan las cosas y sentirte capaz, cuidando tu tiempo, tu energía y tu espacio.',
    strengths: [
      'Investiga a fondo antes de opinar',
      'Mantiene la cabeza fría cuando hay tensión',
      'Se arregla bien por su cuenta',
      'Aporta ideas que otros no vieron',
      'Escucha y observa con atención',
    ],
    tensions: [
      'Puede tomar distancia de lo que siente',
      'Le cuesta pedir o mostrar lo que necesita',
      'Tiende a analizar en lugar de actuar',
      'Puede alejarse de los demás cuando se siente exigido',
      'Comparte poco de su vida personal',
    ],
    growth:
      'En crecimiento, te animás a actuar con lo que ya sabés y a compartir más de vos con las personas en las que confiás.',
    stress:
      'Bajo estrés, podés replegarte, guardar tu energía y quedarte pensando en lugar de involucrarte.',
    triad: 'mind',
    color: '--nureon-type-5',
    page: {
      strengths: [
        'Se vuelve experto en los temas que le interesan.',
        'Piensa con independencia, sin seguir a la mayoría.',
        'Analiza los problemas con objetividad.',
        'Respeta el espacio y los tiempos de los demás.',
      ],
      weaknesses: [
        'Puede acumular información y postergar el momento de usarla.',
        'Le cuesta participar de situaciones sociales intensas.',
        'Puede dejar en segundo plano lo que siente frente a lo que piensa.',
      ],
      growth: [
        'Toma la iniciativa y se hace escuchar.',
        'Defiende sus ideas en voz alta y con firmeza.',
        'Se conecta con su energía física y con el presente.',
      ],
      tensions: [
        'Se dispersa: salta de un tema a otro sin terminar ninguno.',
        'Busca distracciones para no enfrentar lo que le preocupa.',
        'Pierde la calma analítica que suele tener.',
      ],
    },
  },
  6: {
    title: 'El Leal',
    summary: 'Responsable, previsor, solidario y comprometido con su grupo.',
    coreMotivation:
      'Te mueve sentirte seguro y respaldado, y por eso te preparás para lo que pueda salir mal y cuidás tus vínculos.',
    strengths: [
      'Cumple con lo que se compromete',
      'Anticipa los problemas antes de que pasen',
      'Defiende a los suyos cuando hace falta',
      'Trabaja bien en equipo',
      'Es alguien con quien se puede contar',
    ],
    tensions: [
      'Puede preocuparse de más',
      'Duda de sus propias decisiones',
      'Tiende a desconfiar de lo que no conoce',
      'Busca la aprobación de otros antes de avanzar',
      'Puede imaginar el peor resultado posible',
    ],
    growth:
      'En crecimiento, confiás en tu propio criterio, y la seguridad que buscabas afuera la encontrás en vos.',
    stress:
      'Bajo estrés, podés llenarte de dudas y dar muchas vueltas antes de decidir.',
    triad: 'mind',
    color: '--nureon-type-6',
    page: {
      strengths: [
        'Sostiene los vínculos a lo largo del tiempo.',
        'Hace las preguntas incómodas que evitan errores.',
        'Construye comunidad y cuida al grupo.',
        'Pone mucho esfuerzo en las causas en las que cree.',
      ],
      weaknesses: [
        'Oscila entre desconfiar de la autoridad y necesitar apoyarse en ella.',
        'La ansiedad puede hacerle ver amenazas donde no las hay.',
        'Puede reaccionar con escepticismo ante ideas nuevas.',
      ],
      growth: [
        'Confía más en que las cosas pueden salir bien.',
        'Baja la guardia y disfruta del presente.',
        'Escucha otros puntos de vista sin ponerse a la defensiva.',
      ],
      tensions: [
        'Se sobreexige y se llena de tareas para no sentir miedo.',
        'Se preocupa por la imagen y por demostrar que puede.',
        'Puede actuar con apuro y sin escuchar a nadie.',
      ],
    },
  },
  7: {
    title: 'El Entusiasta',
    summary: 'Alegre, inquieto, versátil y con muchas ganas de vivir cosas nuevas.',
    coreMotivation:
      'Te mueve sentirte libre y con opciones abiertas, y buscás lo que te entusiasma para no quedar atrapado en lo que duele o aburre.',
    strengths: [
      'Contagia buen humor',
      'Ve oportunidades donde otros ven problemas',
      'Se interesa por muchos temas',
      'Arranca proyectos con mucha energía',
      'Se acomoda rápido a los cambios',
    ],
    tensions: [
      'Le cuesta terminar lo que empieza',
      'Puede esquivar las conversaciones incómodas',
      'A veces decide sin medir las consecuencias',
      'Se aburre rápido de la rutina',
      'Puede abarcar más de lo que puede sostener',
    ],
    growth:
      'En crecimiento, te quedás con lo que elegiste aunque deje de ser novedad, y encontrás satisfacción en profundizar.',
    stress:
      'Bajo estrés, podés sentirte encerrado por tus compromisos y perder la paciencia cuando las cosas no salen como las imaginabas.',
    triad: 'mind',
    color: '--nureon-type-7',
    page: {
      strengths: [
        'Genera ideas nuevas con facilidad.',
        'Encara la vida con optimismo y curiosidad.',
        'Conecta temas y personas que no parecían tener nada en común.',
        'Aporta energía y ligereza a los momentos tensos.',
      ],
      weaknesses: [
        'Puede saltar de un plan a otro sin detenerse en ninguno.',
        'Evita el malestar llenándose de planes.',
        'Le cuesta comprometerse cuando eso implica cerrar otras opciones.',
      ],
      growth: [
        'Se detiene en una cosa en vez de picotear de todo.',
        'Disfruta del silencio y la concentración.',
        'Valora lo que ya tiene en lugar de buscar siempre lo próximo.',
      ],
      tensions: [
        'Se vuelve crítico y exigente con los demás.',
        'Se irrita ante los límites y las demoras.',
        'Pasa de la ligereza a la rigidez: todo tiene que ser a su manera.',
      ],
    },
  },
  8: {
    title: 'El Desafiador',
    summary: 'Fuerte, directo, protector y con iniciativa para tomar el mando.',
    coreMotivation:
      'Te mueve sentir que llevás las riendas de tu vida y que nadie puede pasarles por encima ni a vos ni a los tuyos.',
    strengths: [
      'Toma decisiones y se hace cargo',
      'Protege a la gente que quiere',
      'Dice lo que piensa sin vueltas',
      'Pone en marcha lo que otros dudan en empezar',
      'Defiende lo que considera justo',
    ],
    tensions: [
      'Puede imponerse sin darse cuenta',
      'Le cuesta mostrarse frágil',
      'Prefiere no depender de nadie',
      'Puede reaccionar con demasiada intensidad',
      'Tiene poca paciencia con la indecisión',
    ],
    growth:
      'En crecimiento, usás tu fuerza para cuidar más que para controlar, y te permitís mostrar tu lado más sensible.',
    stress:
      'Bajo estrés, podés ponerte a la defensiva y endurecerte cuando sentís que las cosas se te van de las manos.',
    triad: 'instinct',
    color: '--nureon-type-8',
    page: {
      strengths: [
        'Transmite firmeza en los momentos difíciles.',
        'No se achica ante los conflictos.',
        'Tiene una energía enorme para llevar adelante lo que se propone.',
        'Da la cara por quienes tienen menos poder.',
      ],
      weaknesses: [
        'Puede vivir los desacuerdos como una pelea de poder.',
        'Muestra enojo con más facilidad que tristeza o miedo.',
        'Puede excederse: trabaja, discute o disfruta sin medida.',
        'Tarda en confiar y pone a prueba a los demás.',
      ],
      growth: [
        'Pone su energía al servicio de otras personas.',
        'Descubre que mostrar afecto también es una forma de fortaleza.',
        'Escucha antes de decidir y les deja lugar a otros.',
      ],
      tensions: [
        'Se aísla para recuperar el control.',
        'Se guarda lo que piensa y desconfía de todos.',
        'Deja de actuar y se queda rumiando estrategias.',
      ],
    },
  },
  9: {
    title: 'El Pacificador',
    summary: 'Sereno, paciente, abierto y con facilidad para acercar a las personas.',
    coreMotivation:
      'Te mueve sentirte en paz, por dentro y con los demás, y por eso evitás lo que pueda generar tensiones.',
    strengths: [
      'Escucha sin juzgar',
      'Entiende puntos de vista muy distintos',
      'Calma los ánimos en un conflicto',
      'Hace que los demás se sientan cómodos',
      'Es constante y paciente',
    ],
    tensions: [
      'Puede postergar lo que le importa',
      'Le cuesta decir lo que quiere',
      'Cede para no generar conflictos',
      'Se deja llevar por la rutina o por lo que deciden otros',
      'Le cuesta poner prioridades',
    ],
    growth:
      'En crecimiento, te hacés lugar a vos mismo: decís lo que pensás y avanzás con lo que querés, sin perder la calma.',
    stress:
      'Bajo estrés, podés desconectarte y dejar pasar las cosas en lugar de enfrentarlas.',
    triad: 'instinct',
    color: '--nureon-type-9',
    page: {
      strengths: [
        'Su presencia transmite tranquilidad.',
        'Ayuda a que un grupo llegue a acuerdos.',
        'Acepta a las personas como son.',
        'Se adapta con flexibilidad a lo que va pasando.',
      ],
      weaknesses: [
        'Evita lo incómodo aunque eso le traiga problemas después.',
        'Se pierde en tareas menores y deja lo importante para más adelante.',
        'Le cuesta mostrar enojo, aun cuando tiene motivos.',
        'Puede minimizar sus opiniones para no desentonar.',
      ],
      growth: [
        'Se pone en movimiento y persigue sus propias metas.',
        'Confía en lo que aporta y lo muestra.',
        'Toma decisiones con más energía y foco.',
      ],
      tensions: [
        'Se llena de preocupaciones y ve riesgos por todos lados.',
        'Duda de todo, incluso de lo que antes tenía claro.',
        'Se resiste en silencio: dice que sí y después no lo hace.',
      ],
    },
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
