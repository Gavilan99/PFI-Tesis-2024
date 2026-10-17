# -*- coding: utf-8 -*-
# Centros de Inteligencia — Cuerpo / Corazon / Mente
# origin: R = reworked from Anexo C, N = net-new
SYSTEM = "Centros de Inteligencia"
GROUPS = ["Cuerpo", "Corazón", "Mente"]
# Member types per group. Used by build.py to default and validate `type_coverage`.
GROUP_TYPES = {"Cuerpo": [8, 9, 1], "Corazón": [2, 3, 4], "Mente": [5, 6, 7]}

# (origin, source_note, prompt, type, options[(text, group)])
ITEMS = [
("R", "Anexo C #1 — reencuadrado de reacción conductual a impulso motivacional",
 "Cuando alguien señala un error tuyo delante de otros, lo primero que se activa en vos es:", "scenario",
 [("Un impulso de responder y no quedar en posición de debilidad", "Cuerpo"),
  ("La incomodidad de imaginar cómo te ven ahora los demás", "Corazón"),
  ("La necesidad de determinar si la observación es correcta", "Mente")]),

("R", "Anexo C #2 — 'confío en' era ambiguo; ahora apunta al punto de apoyo interno",
 "Bajo presión y sin margen de tiempo, ¿en qué te apoyás para decidir?", "scenario",
 [("En lo que el cuerpo te indica antes de razonarlo", "Cuerpo"),
  ("En cómo la situación te hace sentir y qué te dice eso", "Corazón"),
  ("En ordenar lógicamente lo que sabés hasta que aparezca la salida", "Mente")]),

("R", "Anexo C #3 — de 'preocupación' genérica a intolerancia específica",
 "Frente a una decisión difícil, lo que más te cuesta tolerar es:", "scenario",
 [("Quedarte quieto sin poder hacer nada todavía", "Cuerpo"),
  ("Que alguien salga lastimado por lo que decidas", "Corazón"),
  ("Avanzar sabiendo que te falta información", "Mente")]),

("R", "Anexo C #4 — corrige el error tipográfico 'defenterte' y apunta al sostén de la postura",
 "Cuando tenés que defender tu posición, ¿qué la sostiene realmente?", "scenario",
 [("Una convicción visceral sobre lo que está bien y lo que no", "Cuerpo"),
  ("El vínculo con las personas involucradas", "Corazón"),
  ("Un razonamiento que podés justificar paso a paso", "Mente")]),

("R", "Anexo C #5 — de capacidad autopercibida a confianza en el imprevisto",
 "Ante un imprevisto que te descoloca, ¿qué capacidad tuya sentís más confiable?", "scenario",
 [("Tu capacidad de reaccionar sin pensarlo demasiado", "Cuerpo"),
  ("Tu capacidad de leer el clima emocional y adaptarte", "Corazón"),
  ("Tu capacidad de entender rápido qué está pasando", "Mente")]),

("R", "Anexo C #6 — de reacción observable a destino del enojo",
 "Cuando aparece el enojo, lo que hacés con él es:", "scenario",
 [("Sacarlo afuera; se nota enseguida", "Cuerpo"),
  ("Guardarlo y procesar que te dolió realmente", "Corazón"),
  ("Analizarlo hasta entender de dónde salió", "Mente")]),

("R", "Anexo C #7 — de respuesta típica a mecanismo de alivio",
 "Cuando la ansiedad aparece, tu manera de aliviarla es:", "scenario",
 [("Moverte, hacer algo concreto", "Cuerpo"),
  ("Buscar calmar lo que estás sintiendo", "Corazón"),
  ("Entender su origen para desactivarla", "Mente")]),

("R", "Anexo C #8 — contextualizado a gente desconocida; foco atencional",
 "En una conversación con gente que no conocés, tu atención se va principalmente a:", "scenario",
 [("Marcar presencia y ocupar tu lugar", "Cuerpo"),
  ("El vínculo que se arma con cada persona", "Corazón"),
  ("Entender las reglas implícitas del grupo", "Mente")]),

("R", "Anexo C #9 — de 'preocupación' a condición innegociable",
 "Al armar un plan, lo que no podés dejar sin resolver es:", "scenario",
 [("Que esté todo listo para arrancar", "Cuerpo"),
  ("Que los demás queden conformes con vos", "Corazón"),
  ("Qué hacer si algo falla", "Mente")]),

("R", "Anexo C #10 — apunta explícitamente al motor detrás del logro",
 "Detrás de tu deseo de lograr algo importante, lo que hay es:", "scenario",
 [("Hacer algo que sentís propio y coherente con tu criterio", "Cuerpo"),
  ("Que eso diga algo sobre quién sos", "Corazón"),
  ("Sentir que ahora entendés mejor por dónde seguir", "Mente")]),

("R", "Anexo C #11 — reducido a lo que moviliza, sin describir la conducta",
 "En un conflicto abierto, lo que te moviliza es:", "scenario",
 [("Proteger lo tuyo y a quienes dependen de vos", "Cuerpo"),
  ("Que no se rompa el vínculo", "Corazón"),
  ("Entender la lógica del problema para desarmarlo", "Mente")]),

("N", "", "Al final de un día muy exigente, lo que más necesitás para recuperarte es:", "scenario",
 [("Descargar el cuerpo de alguna manera", "Cuerpo"),
  ("Hablar con alguien que te entienda", "Corazón"),
  ("Ordenar la cabeza hasta que el día deje de dar vueltas", "Mente")]),

("N", "", "Cuando algo te sale mal, la primera pregunta que te hacés es:", "scenario",
 [("¿Qué hago ahora?", "Cuerpo"),
  ("¿Qué dice esto de mi?", "Corazón"),
  ("¿Dónde estuvo el error?", "Mente")]),

("N", "", "Lo que más te desgasta de una espera larga es:", "scenario",
 [("No poder hacer nada al respecto", "Cuerpo"),
  ("No saber cómo va a afectar a los que te importan", "Corazón"),
  ("No tener datos suficientes para anticipar el desenlace", "Mente")]),

("N", "", "Cuando conocés a alguien nuevo, lo que registrás primero es:", "scenario",
 [("Si es alguien confiable, aunque no sepas explicar por qué", "Cuerpo"),
  ("Cómo se siente esa persona en ese momento", "Corazón"),
  ("Qué tipo de persona es y cómo encaja con el resto", "Mente")]),

("N", "", "Cuando tenés que pedir ayuda, lo que más te cuesta es:", "scenario",
 [("Ceder autonomía sobre algo que era tuyo", "Cuerpo"),
  ("Sentir que te convertís en una carga", "Corazón"),
  ("Admitir en voz alta que no lo tenías resuelto", "Mente")]),

("N", "", "Frente a una injusticia que no te afecta directamente, lo primero que aparece es:", "scenario",
 [("Bronca inmediata, casi física", "Cuerpo"),
  ("Dolor por quien la está sufriendo", "Corazón"),
  ("La necesidad de entender cómo se llegó a eso", "Mente")]),

("N", "", "Lo que más valorás de alguien que te acompaña en un mal momento es:", "scenario",
 [("Que esté ahí y haga lo que haya que hacer", "Cuerpo"),
  ("Que entienda cómo te sentís sin que tengas que explicarlo", "Corazón"),
  ("Que te ayude a ver la situación con más claridad", "Mente")]),

("N", "", "Cuando algo te entusiasma de verdad, lo notas porque:", "scenario",
 [("El cuerpo se activa y querés arrancar ya", "Cuerpo"),
  ("Necesitás contárselo a alguien", "Corazón"),
  ("No podés dejar de pensar en cómo funcionaria", "Mente")]),

("N", "", "Si algo importante depende de vos y todavía no está resuelto, lo que aparece es:", "scenario",
 [("Inquietud física hasta que lo resuelvas", "Cuerpo"),
  ("Preocupación por defraudar a alguien", "Corazón"),
  ("La cabeza dando vueltas sobre los escenarios posibles", "Mente")]),

("N", "", "Cuando alguien te elogia, tu reacción interna más honesta es:", "scenario",
 [("Restarle importancia y seguir", "Cuerpo"),
  ("Sentir que algo se acomoda por dentro", "Corazón"),
  ("Evaluar si el elogio es preciso o exagerado", "Mente")]),

("N", "", "Al elegir entre dos caminos igual de válidos, lo que termina inclinando la balanza es:", "scenario",
 [("Cuál de los dos te resulta más natural hacer", "Cuerpo"),
  ("Cuál deja mejor parados a los que están involucrados", "Corazón"),
  ("Cuál resiste mejor un análisis frío", "Mente")]),

("N", "", "Lo que más te incomoda de una reunión improvisada es:", "scenario",
 [("Quedarte con la energía trabada, sin poder hacer nada", "Cuerpo"),
  ("Que haya tensión entre los presentes", "Corazón"),
  ("Llegar sin haber podido preparar nada", "Mente")]),

("N", "", "Cuando te equivocás en público, lo que más te cuesta soltar después es:", "scenario",
 [("La sensación de haber quedado expuesto", "Cuerpo"),
  ("La imagen que quedó de vos en los demás", "Corazón"),
  ("El repaso mental de como podrías haberlo evitado", "Mente")]),

("N", "", "Si tuvieras que describir de dónde viene tu seguridad, dirías que viene de:", "scenario",
 [("Saber que estás parado donde te parece correcto estar", "Cuerpo"),
  ("Saber que lo que sos vale algo para alguien", "Corazón"),
  ("Saber que tenés una idea clara de lo que puede pasar", "Mente")]),

("N", "", "Frente a una oportunidad que aparece de golpe, tu primer movimiento es:", "scenario",
 [("Algo en vos ya sabe si te conviene o no", "Cuerpo"),
  ("Pensás enseguida a quiénes afecta y cómo quedás", "Corazón"),
  ("Se te abren las preguntas de qué implicaría", "Mente")]),

("N", "", "Lo que menos tolerarías en un equipo de trabajo es:", "scenario",
 [("Que las cosas se hagan de un modo que te resulta incorrecto", "Cuerpo"),
  ("Que no se reconozca lo que cada uno pone", "Corazón"),
  ("Que nadie tenga claro hacia dónde se va", "Mente")]),

("N", "", "Cuando algo te da miedo, lo que hacés con ese miedo es:", "scenario",
 [("Se te tensa el cuerpo y querés resolverlo ya", "Cuerpo"),
  ("Te preguntás qué dice ese miedo de vos", "Corazón"),
  ("Le buscás forma hasta que deje de ser difuso", "Mente")]),

("N", "", "Lo que más te cuesta de trabajar con alguien muy distinto a vos es:", "scenario",
 [("Su ritmo, cuando no coincide con el tuyo", "Cuerpo"),
  ("No poder leer bien qué le pasa", "Corazón"),
  ("No entender su forma de razonar", "Mente")]),

("N", "", "Cuando tenés que dar una noticia difícil, tu preocupación principal es:", "scenario",
 [("Decirlo de una vez y no dilatarlo", "Cuerpo"),
  ("Cómo le va a caer a quien la recibe", "Corazón"),
  ("Haber ordenado bien que vas a decir", "Mente")]),

("N", "", "Lo que te haría sentir que un día valió la pena es:", "scenario",
 [("Haber hecho algo concreto", "Cuerpo"),
  ("Haber tenido un momento genuino con alguien", "Corazón"),
  ("Haber entendido algo que antes no entendías", "Mente")]),

("N", "", "Cuando alguien invade tu espacio, lo que se activa primero es:", "scenario",
 [("Una reacción inmediata de poner límite", "Cuerpo"),
  ("La duda sobre si está bien incomodarse", "Corazón"),
  ("El cálculo de cómo resolverlo sin conflicto", "Mente")]),

("N", "", "Si tuvieras que renunciar a una de estas, la última que soltarías sería:", "scenario",
 [("Tu independencia para hacer lo que considerás", "Cuerpo"),
  ("Los vínculos que construiste", "Corazón"),
  ("La certeza de entender lo que te rodea", "Mente")]),

("N", "", "Al empezar algo completamente nuevo, lo que más te cuesta es:", "scenario",
 [("La torpeza inicial, no dominarlo todavía", "Cuerpo"),
  ("Sentirte evaluado mientras aprendés", "Corazón"),
  ("No tener todavía un mapa mental de cómo funciona", "Mente")]),

("N", "", "Lo que más te agota de una discusión larga es:", "scenario",
 [("La tensión acumulada en el cuerpo", "Cuerpo"),
  ("El desgaste del vínculo", "Corazón"),
  ("Dar vueltas sobre lo mismo sin conclusión", "Mente")]),

("N", "", "Cuando algo importante sale bien, lo que te da más satisfacción es:", "scenario",
 [("Haberlo sostenido hasta el final", "Cuerpo"),
  ("Que se note lo que pusiste ahí", "Corazón"),
  ("Que la estrategia haya funcionado como pensabas", "Mente")]),

("N", "", "Frente a una regla que te parece absurda, tu impulso es:", "scenario",
 [("Ignorarla y hacer lo que corresponde", "Cuerpo"),
  ("Ver a quién afecta antes de moverte", "Corazón"),
  ("Entender por qué existe antes de juzgarla", "Mente")]),

("N", "", "Si te ofrecen un desafío grande, lo que necesitás saber antes de aceptar es:", "scenario",
 [("Si vas a tener libertad para manejarlo a tu modo", "Cuerpo"),
  ("Con quiénes vas a trabajar", "Corazón"),
  ("En qué consiste exactamente", "Mente")]),

("N", "", "En una crisis, el rol que naturalmente ocupás es:", "scenario",
 [("El que responde con el cuerpo antes de tener un plan", "Cuerpo"),
  ("El que registra cómo está cada uno", "Corazón"),
  ("El que arma el mapa de lo que está pasando", "Mente")]),

("N", "", "Al tomar una decisión de la que después te arrepentís, lo que solías haber ignorado era:", "scenario",
 [("Una senal física de que algo no estaba bien", "Cuerpo"),
  ("Lo que sentías respecto de las personas involucradas", "Corazón"),
  ("Un dato que estaba a la vista", "Mente")]),

# --- Likert (5 opciones ordenadas de acuerdo) ---
("N", "", "Cuando algo no me cierra, lo siento en el cuerpo antes de poder explicarlo con palabras.", "likert", "Cuerpo"),
("N", "", "Me cuesta quedarme quieto mientras hay un problema sin resolver.", "likert", "Cuerpo"),
("N", "", "Prefiero equivocarme actuando que acertar después de haber esperado demasiado.", "likert", "Cuerpo"),
("N", "", "Cuando alguien me falta el respeto, mi reacción sale antes de que alcance a pensarla.", "likert", "Cuerpo"),
("N", "", "Me importa más de lo que admito cómo me perciben los demás.", "likert", "Corazón"),
("N", "", "Me doy cuenta del estado de ánimo de alguien apenas entra a un lugar.", "likert", "Corazón"),
("N", "", "Cuando alguien se aleja de mí, me cuesta no tomarlo como algo personal.", "likert", "Corazón"),
("N", "", "Antes de comprometerme con algo, necesito haber pensado que podría salir mal.", "likert", "Mente"),
("N", "", "Me tranquiliza tener más información, incluso cuando sé que no la voy a usar.", "likert", "Mente"),
("N", "", "Suelo repasar mentalmente conversaciones que ya terminaron.", "likert", "Mente"),
]
