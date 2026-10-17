# -*- coding: utf-8 -*-
"""Prototype v4.1 — Conjunto Horneviano (6 items) + lote 1 (12 items).

Source: [[NureonAI Prototype v4.1 — Transcribed Corrections]].
H5 is the only item whose options are in subjunctive, because its stem ends in
"lo más probable es que:". Deliberate, per the v4 review.
"""
from horneviano import SYSTEM, GROUPS, GROUP_TYPES  # noqa: F401

ITEMS = [
("N", "v4.1 H1",
 "Cuando querés algo que depende de otra persona, lo que hacés es:", "scenario",
 [("Ir directo a pedir lo que querés", "Asertiva"),
  ("Hacer primero lo que sentís que corresponde antes de pedir algo para vos", "Complaciente"),
  ("Tomar distancia un tiempo antes de exponerte a pedirlo", "Retraída")]),

("N", "v4.1 H2",
 "Cuando algo te bloquea el camino, tu manera de actuar es:", "scenario",
 [("Tomar la iniciativa y buscar cómo destrabar el camino", "Asertiva"),
  ("Ver qué te toca hacer en esa situación y cumplirlo", "Complaciente"),
  ("Hacerte a un lado, dejar que decante y volver después", "Retraída")]),

("N", "v4.1 H3",
 "En un grupo donde no te sentís cómodo, lo que hacés es:", "scenario",
 [("Meterte de lleno y buscar activamente tu lugar", "Asertiva"),
  ("Ubicar cómo se maneja el grupo y seguir esa forma", "Complaciente"),
  ("Quedarte en la tuya hasta sentirte más ubicado", "Retraída")]),

("N", "v4.1 H4",
 "De una etapa con mucha exigencia encima, lo que menos tolerarías es:", "scenario",
 [("Que todo el tiempo algo te frene de avanzar con lo tuyo", "Asertiva"),
  ("Quedarte con la sensación de no haber cumplido con lo que esperaban de vos", "Complaciente"),
  ("Que no te quede un rato a solas para acomodar las cosas", "Retraída")]),

("N", "v4.1 H5",
 "Si alguien en el trabajo toma una decisión que te afecta sin tenerte en cuenta, lo más probable es que:", "scenario",
 [("Tomes la iniciativa para cambiar la situación y recuperar margen de acción", "Asertiva"),
  ("Revises qué parte era tuya y a quién más le complicó la decisión, antes de plantearlo", "Complaciente"),
  ("Te corras un poco de la situación, la proceses por tu cuenta y decidas después si volvés sobre el tema", "Retraída")]),

("N", "v4.1 H6",
 "Cuando te dan una tarea que no te interesa, lo que hacés es:", "scenario",
 [("Intentar renegociar la tarea para llevarla hacia algo que te cierre más", "Asertiva"),
  ("Hacerla porque entendés que te toca, aunque no te interese", "Complaciente"),
  ("Resolver lo necesario sin poner demasiado de vos y después volver a lo tuyo", "Retraída")]),

# ---------------------------------------------------------------------------
# Lote 1, filas 1-12 de escenario.
# Fuente: [[Lote Horneviano 1-12 — Adjudicación y set corregido]].
# Spec:   [[Spec de Conjunto — Horneviano (v3, final)]], auditada dos veces antes de escribir.
#
# Redacción ciega en paralelo por dos motores desde la misma spec; adjudicada 10-1-1 y luego
# corregida sobre el set ganador. La faceta Retraída de la fila 2 pasó de "espacio propio" a
# "ritmo propio" durante la adjudicación — el defecto estaba en la spec, no en la redacción.
#
# El comentario de cada ítem es valencia · facetas en orden Asertiva / Complaciente / Retraída.

# hornev1 01 — aproximación · ir por lo deseado / compromiso · interna / procesar
("N", "hornev1 01",
 'Cuando algo que querías hace tiempo se vuelve posible, lo primero que se te viene es:', "scenario",
 [('Las ganas de arrancar antes de que se cierre la ventana', 'Asertiva'),
  ('Todo lo que quedaría sin resolver si te ponés con esto', 'Complaciente'),
  ('La necesidad de asimilarlo antes de hacer nada', 'Retraída')]),

# hornev1 02 — aproximación · ganar margen / lo que corresponde · compromiso asumido / ritmo propio
("N", "hornev1 02",
 'Cuando te ofrecen sumarte a algo que te interesa, lo que más mirás antes de decir que sí es:', "scenario",
 [('Cuánto vas a poder llevarlo hacia donde vos querés', 'Asertiva'),
  ('Con qué te habías comprometido antes de que apareciera esto', 'Complaciente'),
  ('Si vas a poder ir a tu ritmo o al del resto', 'Retraída')]),

# hornev1 03 — aproximación · iniciativa / necesidades ajenas · necesidad concreta / volver después
("N", "hornev1 03",
 'Cuando estás armando un proyecto con otra gente, lo que más define cómo te involucrás es:', "scenario",
 [('Cuánto ves que podés proponer e impulsar lo que te interesa', 'Asertiva'),
  ('Que dependa de vos algo que otro del grupo realmente necesita', 'Complaciente'),
  ('Poder salir un rato de la conversación y volver con algo pensado', 'Retraída')]),

# hornev1 04 — aproximación · avance / referencias · norma o rol / decantar
("N", "hornev1 04",
 'Cuando empezás a aprender algo que elegiste vos, lo que más te cuesta al principio es:', "scenario",
 [('Notar que avanzás demasiado lento para las ganas que tenés de seguir', 'Asertiva'),
  ('No tener una regla clara de cómo se hace lo que elegiste', 'Complaciente'),
  ('Que lo que estás aprendiendo todavía no termine de asentarse', 'Retraída')]),

# hornev1 05 — aproximación · ir por lo deseado / responsabilidad · interna / preservar interioridad
("N", "hornev1 05",
 'Si te queda por delante una semana sin obligaciones, lo que más te ocupa es:', "scenario",
 [('Todo lo que por fin podrías dedicarle a algo que venís queriendo', 'Asertiva'),
  ('Lo que sentís pendiente aunque nadie esté esperando que lo hagas', 'Complaciente'),
  ('Tener tiempo sin demandas para volver a saber qué querés', 'Retraída')]),

# hornev1 06 — aproximación · tomar acción / compromiso · compromiso asumido / distancia
("N", "hornev1 06",
 'Cuando alguien te propone hacer algo juntos, lo primero que tenés en cuenta es:', "scenario",
 [('Las ganas que te da ponerlo en marcha si te entusiasma', 'Asertiva'),
  ('Qué compromiso implicaría para vos aceptar esa propuesta', 'Complaciente'),
  ('Cuánto necesitás despegarte un poco antes de contestar', 'Retraída')]),

# hornev1 07 — aproximación · modificar la situación / deber · interna / bajar activación
("N", "hornev1 07",
 'Cuando conseguís algo que querías y ahora hay que sostenerlo, lo que más te ocupa es:', "scenario",
 [('Qué tendrías que mover para que siga acercándose a lo que querés', 'Asertiva'),
  ('Todo lo que sentís que te toca mantener por haberlo elegido', 'Complaciente'),
  ('Bajar un poco la intensidad para poder seguir sin fundirte', 'Retraída')]),

# hornev1 08 — aproximación · ir por lo deseado / lo que corresponde · compromiso asumido / decantar
("N", "hornev1 08",
 'Cuando aparece una oportunidad que no buscabas pero te tienta, lo que más termina inclinando la balanza es:', "scenario",
 [('Cuánto te tira aprovecharla porque te dan ganas de ir por eso', 'Asertiva'),
  ('Qué compromisos que ya asumiste quedarían tironeados si la aceptás', 'Complaciente'),
  ('Necesitar darle unos días antes de saber si la querés', 'Retraída')]),

# hornev1 09 — neutral · ganar margen / deber · norma o rol / menor involucramiento
("N", "hornev1 09",
 'Cuando hay que repartir tareas en un grupo, lo que menos tolerarías es:', "scenario",
 [('Terminar afuera de la parte que más te interesa', 'Asertiva'),
  ('Que queden tareas sin una referencia clara de a quién le corresponde cada una', 'Complaciente'),
  ('Que el reparto te deje involucrado en demasiadas cosas al mismo tiempo', 'Retraída')]),

# hornev1 10 — neutral · avance / responsabilidad · interna / volver después
("N", "hornev1 10",
 'Cuando tenés varias cosas encima al mismo tiempo, lo que más te pesa es:', "scenario",
 [('Notar que ninguna de esas cosas avanza hacia donde querés llevarla', 'Asertiva'),
  ('Que haya cosas que sentís tuyas y queden esperándote', 'Complaciente'),
  ('No poder dejar una de lado un rato y retomarla con más claridad', 'Retraída')]),

# hornev1 11 — neutral · tomar acción / lo que corresponde · interna / preservar interioridad
("N", "hornev1 11",
 'Cuando alguien te pide opinión sobre algo suyo, lo que más te condiciona es:', "scenario",
 [('Cuánto podría cambiar algo que te importa si se lo decís', 'Asertiva'),
  ('Lo que sentís que corresponde decir, aunque no sea lo más cómodo para vos', 'Complaciente'),
  ('Necesitar un poco de distancia para no contestar en caliente', 'Retraída')]),

# hornev1 12 — neutral · ganar margen / necesidades ajenas · necesidad concreta / menor involucramiento
("N", "hornev1 12",
 'Cuando tenés que decidir cuánto involucrarte en un problema que no es tuyo, lo que más te pesa es:', "scenario",
 [('Entrar en algo donde no vas a cambiar gran cosa', 'Asertiva'),
  ('Saber que hay una necesidad concreta y sentir que eso te compromete', 'Complaciente'),
  ('No poder frenar a tiempo cuando ya te metiste demasiado', 'Retraída')]),


# ---------------------------------------------------------------------------
# Lote mixto v4, filas 13-18.
# Fuente: [[Lote mixto v4 — Adjudicación y set consolidado]]
# Spec:   [[Spec de Lote Mixto — v4, post-auditoría del rediseño]]
#
# Tercer intento del lote: la v2 se descartó entera (doce dominios con un solo esquema) y la v3
# volvió NO-GO en auditoría. Los dominios de la v4 se aprobaron sin duplicaciones.
# Redacción ciega en paralelo, adjudicada 7-3-2 con dos filas mixtas.
# El comentario de cada ítem es valencia · facetas en orden de columna.

# H13 — amenaza · tomar acción / lo que corresponde · norma o rol / procesar
("N", "hornev2 13",
 'Cuando un plan con un amigo se cancela por tercera vez seguida, lo primero que te aparece es:', "scenario",
 [('Que el próximo plan vuelva a quedar en el aire sin que puedas mover algo para evitarlo', 'Asertiva'),
  ('La manera de responder que te parece más acorde a esa amistad antes de decidir si insistís', 'Complaciente'),
  ('Un poco de distancia de esa persona para registrar qué te dejó la tercera cancelación', 'Retraída')]),

# H14 — neutral · ganar margen / pauta o criterio externo · norma o rol / distancia
("N", "hornev2 14",
 'Cuando en un viaje con amigos tienen que acordar cada mañana qué hacer ese día, lo que más te condiciona es:', "scenario",
 [('Cuánto vas a tener que resignar de lo que vos querías ver', 'Asertiva'),
  ('No tener una forma clara de decidir cuando no coinciden', 'Complaciente'),
  ('Tener que estar todo el día pegado al grupo para que salga', 'Retraída')]),

# H15 — neutral · iniciativa / deber · interna / preservar interioridad
("N", "hornev2 15",
 'Cuando vas a organizar el almuerzo de cumpleaños de un familiar, lo primero que mirás es:', "scenario",
 [('Qué podrías proponer vos para que salga distinto de siempre', 'Asertiva'),
  ('Lo que sabés que va a faltar si no lo mirás vos', 'Complaciente'),
  ('Si te va a quedar algún momento en que no estés atendiendo a alguien', 'Retraída')]),

# H16 — amenaza · modificar la situación / compromiso · compromiso asumido / volver después
("N", "hornev2 16",
 'Cuando el equipo con el que jugás los martes empieza a sumar entrenamientos, lo que más te cuesta es:', "scenario",
 [('Quedarte atado a una semana armada de una manera que ya no te sirve para seguir jugando', 'Asertiva'),
  ('El peso de haber dicho que sí al equipo antes de que aparecieran estos entrenamientos', 'Complaciente'),
  ('Perder la opción de saltearte un par de martes y volver', 'Retraída')]),

# H17 — amenaza · buscar otra vía / necesidades ajenas · necesidad concreta / despejar para pensar
("N", "hornev2 17",
 'Cuando tenés que compartir un gasto grande con gente que no conocés bien, lo primero que mirás es:', "scenario",
 [('Si hay otra forma de arreglarlo que no dependa de todos', 'Asertiva'),
  ('Que otra persona no pueda afrontar la misma parte y eso pese en tu decisión', 'Complaciente'),
  ('Poder sacar la cuenta tranquilo antes de que empiecen a opinar', 'Retraída')]),

# H18 — amenaza · avance / compromiso · compromiso asumido / menor involucramiento
("N", "hornev2 18",
 'Cuando en el trabajo te suman a un chat de grupo que no para de sonar, lo primero que te aparece es:', "scenario",
 [('Notar que tanta conversación frena una tarea que tenés ganas de sacar adelante', 'Asertiva'),
  ('El peso de seguir disponible porque aceptaste formar parte de ese grupo', 'Complaciente'),
  ('Reducir cuánto participás para no quedar absorbido por el ritmo de conversación del grupo', 'Retraída')]),

# --- Likert de Horneviano (12) — cierra el conjunto ------------------------
# Fuente: [[Lote Horneviano Likert v2 — Adjudicación y correcciones]].
# Spec:   [[Spec de Ítems Likert — Horneviano (v1, reescrito)]].
# Segunda redacción; la primera se descartó entera (anclajes-categoría).
# 19: agreement {2,5,6,9} · 23: agreement {5,7,8,9} — ningún miembro del grupo acuerda.
# 21: el revisor lo acepta pero lo deja marcado como el menos convincente del lote.

("N", "hlik 19 · iniciativa · inversa",
 "Durante una reunión que lleva varios minutos sin rumbo y nadie aclaró su propósito, espero tranquilo a que alguien lo defina",
 "likert", ("Asertiva", "inversa")),

("N", "hlik 20 · ganar margen",
 "Si me ofrecen un puesto con mejor sueldo pero con horarios que no me sirven, prefiero negociar las condiciones aunque arriesgue la oferta",
 "likert", "Asertiva"),

("N", "hlik 21 · avance",
 "Que un plan con amigos lleve meses sin fecha me impacienta más de lo que el plan merece",
 "likert", "Asertiva"),

("N", "hlik 22 · tomar acción",
 "Cuando quiero empezar a entrenar y siempre aparece una semana mejor, prefiero arrancar ya antes que esperarla",
 "likert", "Asertiva"),

("N", "hlik 23 · deber interna · inversa",
 "Si tengo un mensaje pendiente que nadie me reclamó, puedo dejarlo para otro día sin que me quede pesando",
 "likert", ("Complaciente", "inversa")),

("N", "hlik 24 · compromiso",
 "Llegado el día de un cumpleaños al que dije que iba y ya no tengo ganas, me pesa más faltar que ir igual",
 "likert", "Complaciente"),

("N", "hlik 25 · responsabilidad",
 "Algo roto lleva días en casa y todos lo esquivan; me pesa dejarlo pendiente aunque no sea mío",
 "likert", "Complaciente"),

("N", "hlik 26 · expectativas",
 "En un trabajo nuevo donde cada uno trabaja distinto, me inquieta no distinguir cuál sería la forma correcta de hacerlo",
 "likert", "Complaciente"),

("N", "hlik 27 · preservar interioridad",
 "Si en el chat del trabajo me preguntan por un tema personal difícil, prefiero contestar por arriba aunque parezca distante",
 "likert", "Retraída"),

("N", "hlik 28 · menor involucramiento",
 "Cuando me invitan a un proyecto que me entusiasma pero me ocuparía los sábados, me frena más de lo que me tienta",
 "likert", "Retraída"),

("N", "hlik 29 · bajar activación",
 "En una discusión que se calienta en una mesa con varias personas, me cuesta seguir hablando sin salirme un rato del cruce",
 "likert", "Retraída"),

("N", "hlik 30 · volver después",
 "Cuando dejo a medias algo que no me sale, vuelvo recién cuando siento que se acomodó solo",
 "likert", "Retraída"),
]
