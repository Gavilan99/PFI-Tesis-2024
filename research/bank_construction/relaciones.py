# -*- coding: utf-8 -*-
# Conjunto de Relaciones Objetales (Armonía) — Apego / Frustración / Rechazo
SYSTEM = "Conjunto de Relaciones Objetales"
GROUPS = ["Apego", "Frustración", "Rechazo"]
# Member types per group. Used by build.py to default and validate `type_coverage`.
GROUP_TYPES = {"Apego": [3, 6, 9], "Frustración": [1, 4, 7], "Rechazo": [2, 5, 8]}

ITEMS = [
("R", "Anexo C #1 — acortado; las opciones originales eran párrafos",
 "En un proyecto grupal, lo que más te importa es:", "scenario",
 [("Que el resultado refleje a todo el grupo", "Apego"),
  ("Que quede a la altura de lo que podría ser", "Frustración"),
  ("Que alguien tome las riendas y no se desarme", "Rechazo")]),

("R", "Anexo C #2 — se conserva el planteo (era de los mejores); opciones más nítidas",
 "En una relación cercana, lo que más temés es:", "scenario",
 [("Que se pierda la conexión", "Apego"),
  ("Que nunca llegue a ser lo que imaginabas", "Frustración"),
  ("Volverte dependiente o perder tu autonomía", "Rechazo")]),

("R", "Anexo C #3 — foco en el motor, sin describir la acción",
 "Ante un desafio grande, lo que te empuja a actuar es:", "scenario",
 [("Que cuenten con vos y no fallarles", "Apego"),
  ("Que las cosas se hagan como corresponde", "Frustración"),
  ("Manejar vos la situación y no depender de nadie", "Rechazo")]),

("R", "Anexo C #4 — de conducta a foco tras el traspié",
 "Cuando un objetivo personal se te frustra, tu atención va a:", "scenario",
 [("Recomponer el equilibrio y que no se desordene todo", "Apego"),
  ("Lo que faltó para que saliera como debía", "Frustración"),
  ("Insistir, porque el objetivo sigue siendo tuyo", "Rechazo")]),

("R", "Anexo C #5 — reduce a la motivación del desacuerdo",
 "Cuando alguien no comparte tu opinión, lo que aparece es:", "scenario",
 [("Ganas de entender su punto para no distanciarse", "Apego"),
  ("Fastidio porque no ven lo que vos ves", "Frustración"),
  ("Sostenerlo sin necesitar que te den la razón", "Rechazo")]),

("R", "Anexo C #6 — opciones acortadas y diferenciadas",
 "Lo que hay detrás de tu impulso de ayudar es:", "scenario",
 [("Querer ser parte importante del grupo", "Apego"),
  ("No soportar ver algo funcionando mal", "Frustración"),
  ("Que puedan contar con vos y eso te de un lugar", "Rechazo")]),

("R", "Anexo C #7 — planteo conservado, opciones más claras",
 "Al entrar a un lugar donde no conocés a nadie, lo que buscás es:", "scenario",
 [("Que te acepten en el grupo", "Apego"),
  ("Encontrar una conversación que valga la pena", "Frustración"),
  ("Dejar claro quién sos y que venís a hacer", "Rechazo")]),

("R", "Anexo C #8 — foco en la motivación primaria, sin describir técnica",
 "Frente a una persona difícil, lo que te guía es:", "scenario",
 [("Encontrar terreno común y bajar la tensión", "Apego"),
  ("Corregir el malentendido que generó todo", "Frustración"),
  ("Poner límites para que no se aprovechen", "Rechazo")]),

("R", "Anexo C #9 — apunta al deseo detrás del cambio",
 "Lo que te impulsa a cambiar algo grande en tu vida es:", "scenario",
 [("Querer un entorno más estable y armonioso", "Apego"),
  ("La insatisfacción con lo que no está a la altura", "Frustración"),
  ("Querer que tu vida sea como vos decidas", "Rechazo")]),

("R", "Anexo C #10 — de 'preocupación' a criterio de evaluacion retrospectiva",
 "Al evaluar decisiones que tomaste, lo que te importa saber es:", "scenario",
 [("Si fortalecieron tus vínculos", "Apego"),
  ("Si fueron las mejores posibles", "Frustración"),
  ("Si te dejaron más dueño de tu vida", "Rechazo")]),

("N", "", "Lo que más te costaría perder es:", "scenario",
 [("Tu lugar entre los tuyos", "Apego"),
  ("La expectativa de algo mejor", "Frustración"),
  ("El control sobre tus propias decisiones", "Rechazo")]),

("N", "", "Cuando algo no está a la altura de lo que esperabas, lo que hacés es:", "scenario",
 [("Acomodarte a lo que hay", "Apego"),
  ("Señalar la diferencia entre lo que es y lo que debería ser", "Frustración"),
  ("Hacerte cargo vos de arreglarlo", "Rechazo")]),

("N", "", "Lo que más te incomoda de depender de alguien es:", "scenario",
 [("Nada, depender de otros es parte de estar vinculado", "Apego"),
  ("Que esa persona no esté a la altura", "Frustración"),
  ("Quedar expuesto si te falla", "Rechazo")]),

("N", "", "En un grupo nuevo, lo primero que tratás de definir es:", "scenario",
 [("Cómo encajás vos ahí", "Apego"),
  ("Si el grupo vale la pena", "Frustración"),
  ("Qué rol vas a ocupar", "Rechazo")]),

("N", "", "Lo que más te frustra de la vida cotidiana es:", "scenario",
 [("Cuando se rompe la armonía de lo que ya funcionaba", "Apego"),
  ("Lo lejos que está de como podría ser", "Frustración"),
  ("Cuando otros deciden por vos", "Rechazo")]),

("N", "", "Cuando alguien se aleja sin explicación, lo que sentís es:", "scenario",
 [("Angustia por la conexión perdida", "Apego"),
  ("Decepción, esperabas otra cosa de esa persona", "Frustración"),
  ("Rechazo, y ganas de adelantarte y alejarte vos", "Rechazo")]),

("N", "", "Lo que buscás en una amistad de años es:", "scenario",
 [("Continuidad y presencia", "Apego"),
  ("Que siga teniendo profundidad", "Frustración"),
  ("Saber que esa persona te necesita tanto como vos a ella", "Rechazo")]),

("N", "", "Si te ofrecen algo bueno pero que te ata, tu reacción es:", "scenario",
 [("Aceptar; la estabilidad tiene valor", "Apego"),
  ("Dudar, porque quizás haya algo mejor", "Frustración"),
  ("Rechazarlo si compromete tu libertad", "Rechazo")]),

("N", "", "Lo que más te define en tus vínculos es:", "scenario",
 [("Que te adaptás para sostenerlos", "Apego"),
  ("Que esperás mucho de ellos", "Frustración"),
  ("Que preferís dar antes que necesitar", "Rechazo")]),

("N", "", "Cuando algo importante depende de otros, lo que sentís es:", "scenario",
 [("Tranquilidad, es normal apoyarse", "Apego"),
  ("Impaciencia si no lo hacen como corresponde", "Frustración"),
  ("Incomodidad por no tenerlo bajo tu control", "Rechazo")]),

("N", "", "Lo que más te duele de un desencuentro es:", "scenario",
 [("La distancia que queda", "Apego"),
  ("Que podría haberse resuelto y no se resolvió", "Frustración"),
  ("Haber quedado en posición de necesitar al otro", "Rechazo")]),

("N", "", "Al imaginar tu vida ideal, lo primero que aparece es:", "scenario",
 [("Rodeado de la gente que querés", "Apego"),
  ("Habiendo alcanzado algo que valga realmente la pena", "Frustración"),
  ("Siendo vos quien puede sostener a los tuyos", "Rechazo")]),

("N", "", "Lo que te hace sentir seguro en una relación es:", "scenario",
 [("Saber que la otra persona no se va a ir", "Apego"),
  ("Saber que hay algo genuino ahí", "Frustración"),
  ("Saber que podrías arreglartelas solo si hiciera falta", "Rechazo")]),

("N", "", "Cuando alguien te pide algo que no podés dar, lo que aparece es:", "scenario",
 [("Culpa por no estar a la altura", "Apego"),
  ("La sensación de que no debería haber llegado a este punto", "Frustración"),
  ("Firmeza para marcar el límite", "Rechazo")]),

("N", "", "Lo que más valorás de alguien es:", "scenario",
 [("Que esté", "Apego"),
  ("Que tenga profundidad", "Frustración"),
  ("Que sea confiable cuando importa", "Rechazo")]),

("N", "", "Frente a un ambiente que no te termina de convencer, lo que hacés es:", "scenario",
 [("Adaptarte y buscar tu lugar igual", "Apego"),
  ("Quedarte con la sensación de que podría ser mejor", "Frustración"),
  ("Marcar tu terreno desde el principio", "Rechazo")]),

("N", "", "Lo que te resulta más difícil de aceptar es:", "scenario",
 [("Que un vínculo se termine", "Apego"),
  ("Que algo se quede a mitad de camino", "Frustración"),
  ("Necesitar ayuda para algo", "Rechazo")]),

("N", "", "Cuando lograste algo importante, lo primero que querés es:", "scenario",
 [("Compartirlo con los tuyos", "Apego"),
  ("Ver si estuvo a la altura de lo que buscabas", "Frustración"),
  ("Saber que lo conseguiste por tu cuenta", "Rechazo")]),

("N", "", "Lo que más te cansa de la gente es:", "scenario",
 [("Cuando se rompe la armonía por cosas chicas", "Apego"),
  ("La mediocridad", "Frustración"),
  ("Que quieran manejarte", "Rechazo")]),

("N", "", "Si tuvieras que empezar de cero en otra ciudad, lo primero sería:", "scenario",
 [("Armar vínculos", "Apego"),
  ("Encontrar algo que valga la pena hacer ahí", "Frustración"),
  ("Asegurarte de poder sostenerte solo", "Rechazo")]),

("N", "", "Lo que más te cuesta de trabajar en algo que no elegiste es:", "scenario",
 [("Nada especial, si el clima es bueno", "Apego"),
  ("Sentir que estás lejos de lo que deberías estar haciendo", "Frustración"),
  ("No haberlo decidido vos", "Rechazo")]),

("N", "", "Cuando alguien te necesita mucho, lo que sentís es:", "scenario",
 [("Que ese vínculo se afianza", "Apego"),
  ("Que ojalá pudiera resolverlo mejor por sí mismo", "Frustración"),
  ("Que ahí tenés un lugar asegurado", "Rechazo")]),

("N", "", "Lo que más influye en como te sentís un día cualquiera es:", "scenario",
 [("Cómo están tus vínculos", "Apego"),
  ("Cuánto te acercaste a lo que querés", "Frustración"),
  ("Cuánto control tuviste sobre tu día", "Rechazo")]),

("N", "", "Frente a una expectativa que no se cumplió, lo que hacés es:", "scenario",
 [("Bajar la expectativa para no sufrir", "Apego"),
  ("Sostenerla igual, aunque duela", "Frustración"),
  ("Dejar de esperar de los demás", "Rechazo")]),

("N", "", "Lo que más te costaría admitir es:", "scenario",
 [("Que necesitás a los demás más de lo que mostrás", "Apego"),
  ("Que nada termina de conformarte", "Frustración"),
  ("Que te da miedo que no te elijan", "Rechazo")]),

("N", "", "En una discusión con alguien querido, lo que priorizás es:", "scenario",
 [("Que la relación salga entera", "Apego"),
  ("Que se resuelva de verdad y no a medias", "Frustración"),
  ("No quedar en desventaja", "Rechazo")]),

("N", "", "Lo que buscás cuando algo te sale bien es:", "scenario",
 [("Que los tuyos lo celebren con vos", "Apego"),
  ("Que haya estado a la altura", "Frustración"),
  ("Que quede claro que fue merito tuyo", "Rechazo")]),

("N", "", "Cuando pensás en tu lugar en el mundo, lo que aparece es:", "scenario",
 [("Con quiénes estás", "Apego"),
  ("Lo que todavía falta", "Frustración"),
  ("Cuánto de eso decidiste vos", "Rechazo")]),

("N", "", "Lo que más te desorienta es:", "scenario",
 [("Quedarte sin referencias afectivas", "Apego"),
  ("Conseguir lo que querías y que no alcance", "Frustración"),
  ("Que otro tome una decisión que te afecta", "Rechazo")]),

("N", "", "Si alguien te ofrece ayuda sin que la pidas, sentís:", "scenario",
 [("Agradecimiento y cercanía", "Apego"),
  ("Que probablemente no la haga como corresponde", "Frustración"),
  ("Cierta incomodidad por quedar en deuda", "Rechazo")]),

("N", "", "Lo que más te importa que reconozcan de vos es:", "scenario",
 [("Que siempre estás", "Apego"),
  ("Que ves lo que otros no ven", "Frustración"),
  ("Que se puede contar con vos", "Rechazo")]),

# --- Likert ---
("N", "", "Me adapto a lo que se espera de mí para no perder mi lugar en el grupo.", "likert", "Apego"),
("N", "", "Me cuesta tomar decisiones que puedan alejarme de la gente que quiero.", "likert", "Apego"),
("N", "", "Prefiero ceder antes que poner en riesgo una relación.", "likert", "Apego"),
("N", "", "Siento que hay algo mejor que todavía no alcancé.", "likert", "Frustración"),
("N", "", "Me decepciona con frecuencia que las cosas no sean como deberían ser.", "likert", "Frustración"),
("N", "", "Tengo una idea bastante clara de como deberían hacerse las cosas.", "likert", "Frustración"),
("N", "", "Me incomoda deberle algo a alguien.", "likert", "Rechazo"),
("N", "", "Prefiero ser quien sostiene a los demás antes que necesitar que me sostengan.", "likert", "Rechazo"),
("N", "", "Me cuesta mostrarme vulnerable, incluso con gente cercana.", "likert", "Rechazo"),
]
