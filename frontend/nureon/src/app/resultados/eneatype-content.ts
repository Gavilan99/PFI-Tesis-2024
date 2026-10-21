import { AccountType } from '../core/models/user.model';

// The result screen's text per eneatype, written for NureonAI: a guide to
// personality centred on motivation, not a diagnosis. The type names are the
// usual ones in the eneagrama literature (and the ones /eneagrama shows); the
// rest is our own wording. `summary` is also the result's descriptionText:
// the backend keeps a copy in app/services/result_descriptions.py, and
// backend/tests/test_result_descriptions.py fails if the two drift apart.
export interface EneatypeContent {
  title: string;
  summary: string;
  coreMotivation: string;
  strengths: string[];
  tensions: string[];
  growth: string;
  stress: string;
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
