# -*- coding: utf-8 -*-
"""Prototype v4.1 — Conjunto Armónico (6 items).

Source: [[NureonAI Prototype v4.1 — Transcribed Corrections]].
A4 Positiva was the only type-flavoured option in v4; the v4.1 rewrite removed it,
so this set has no narrowed `type_coverage` at all.
"""
from armonico import SYSTEM, GROUPS, GROUP_TYPES  # noqa: F401

ITEMS = [
("N", "v4.1 A1",
 "Cuando un amigo la está pasando mal, lo que te sale es:", "scenario",
 [("Ayudarlo a no perder de vista lo bueno que todavía sigue ahí", "Positiva"),
  ("Ordenar juntos el problema y ver qué se puede hacer", "Competente"),
  ("Acompañarlo en lo mal que está sin tratar de sacarlo de ahí enseguida", "Reactiva")]),

("N", "v4.1 A2",
 "Cuando un plan importante se cae sobre la fecha, lo primero que hacés es:", "scenario",
 [("Ver qué de todo lo que habían armado sigue teniendo valor", "Positiva"),
  ("Ordenar lo que queda y buscar una alternativa que funcione", "Competente"),
  ("Parar en lo mal que cayó que todo se viniera abajo, sin pasar directo a rearmar", "Reactiva")]),

("N", "v4.1 A3",
 "Ante un conflicto fuerte en tu familia, lo que priorizás es:", "scenario",
 [("Que la situación no se lleve puesto todo lo bueno", "Positiva"),
  ("Que quede claro cuál es el problema y cómo resolverlo", "Competente"),
  ("Que alguien de la familia diga en voz alta lo mal que se trataron antes de volver a la normalidad", "Reactiva")]),

("N", "v4.1 A4",
 "Después de una etapa mala, lo que te ayuda a arrancar de nuevo es:", "scenario",
 [("Volver a encontrarle valor a algo que ya tenías y se había tapado", "Positiva"),
  ("Tener claro cuál es el próximo paso concreto", "Competente"),
  ("Haber podido registrar lo mal que fue esa etapa, sin que nadie te apurara a dar vuelta la página", "Reactiva")]),

("N", "v4.1 A5",
 "Lo que más te molesta de cómo reacciona la gente ante un problema es:", "scenario",
 [("Que se queden dando vueltas en lo malo sin poder salir", "Positiva"),
  ("Que la reacción emocional del momento les impida ocuparse del problema", "Competente"),
  ("Que actúen como si no hubiera pasado nada", "Reactiva")]),

("N", "v4.1 A6",
 "Si algo te sale mal en el trabajo o el estudio, lo que menos soportás es:", "scenario",
 [("Que eso te arruine el resto de las cosas que van bien", "Positiva"),
  ("No encontrar una forma concreta de arreglarlo", "Competente"),
  ("Tener que hacer como si no hubiera sido para tanto", "Reactiva")]),


# ---------------------------------------------------------------------------
# Lote 1 de Armónico, 11 filas.
# Fuente: [[Lote Armónico 1 — Adjudicación y correcciones]]
# Spec:   [[Spec de Conjunto — Armónico (v3, correcciones de lenguaje)]]
#
# La fila 8 del spec pasó al lote 2 con stem nuevo ("lo primero que necesitás es"): con el stem
# anterior, "lo que más te saca es", las tres opciones quedaban forzadas a ser una queja y una
# queja sobre contaminación se lee como Reactiva, no como Positiva.
#
# Dos filas son de ChatGPT (7, 10), ocho de Claude, y la 7 lleva dos reescrituras del revisor.
# El comentario de cada ítem es valencia · facetas Positiva / Competente / Reactiva.

# arm1 01 — amenaza · conservar vínculo o estabilidad / corregir / validar impacto
("N", "arm1 01",
 'Cuando te olvidás de sacar las entradas que habías dicho que comprabas y la otra persona se entera, lo primero que se te viene es:', "scenario",
 [('Todo lo demás que hay entre ustedes y pesa más que esto', 'Positiva'),
  ('Encontrar la manera de repararlo antes de que se haga más grande', 'Competente'),
  ('No tapar cuánto le molestó tratando de arreglarlo', 'Reactiva')]),

# arm1 02 — amenaza · impedir que lo malo contamine todo / entender / no cerrar demasiado rápido
("N", "arm1 02",
 'Cuando mandás un mensaje que se malentiende y termina en una discusión, lo que más te importa es:', "scenario",
 [('No dejar que un malentendido te cambie el clima del día', 'Positiva'),
  ('Ver en qué parte se malentendió lo que querías decir', 'Competente'),
  ('Que no se cierre con un «ya está» antes de aclararlo de verdad', 'Reactiva')]),

# arm1 05 — amenaza · preservar lo bueno / estructurar / validar impacto
("N", "arm1 05",
 'Cuando un compañero falta varios días por un problema personal y te queda la parte de la entrega que compartían, lo que menos tolerarías es:', "scenario",
 [('Perder de vista lo que sí estaba saliendo bien de ese trabajo', 'Positiva'),
  ('No tener cómo repartir lo que quedó para que entre en la semana', 'Competente'),
  ('Que nadie registre cuánto más te tocó hacer esos días', 'Reactiva')]),

# arm1 06 — amenaza · recuperar perspectiva / encontrar solución / reconocer gravedad
("N", "arm1 06",
 'Cuando te llega una factura mucho más alta de lo habitual y no se entiende de dónde sale la diferencia, lo que más te pesa es:', "scenario",
 [('Pasar el mes entero dándole vueltas a eso y no poder pensar en otra cosa', 'Positiva'),
  ('No encontrar la forma de que alguien lo revise', 'Competente'),
  ('Tener que aceptar que es un detalle cuando para vos no lo es', 'Reactiva')]),

# arm1 07 — amenaza · conservar vínculo o estabilidad / ordenar / no minimizar
("N", "arm1 07",
 'Cuando se te rompe la heladera el mismo mes en que tenías otros gastos grandes, lo que más te ayuda es:', "scenario",
 [('Identificar qué aspectos todavía se mantienen estables después de la rotura', 'Positiva'),
  ('Priorizar los gastos según qué necesita resolverse este mes y qué puede quedar para más adelante', 'Competente'),
  ('Procesar lo fuerte que impacta la rotura en tus gastos antes de empezar a pensar qué hacer', 'Reactiva')]),

# arm1 10 — amenaza · recuperar perspectiva / encontrar solución / validar impacto
("N", "arm1 10",
 'Cuando tu hermana te cuenta que una tormenta le arruinó parte del departamento, lo primero que se te viene es:', "scenario",
 [('Tener en cuenta que, además del daño, quedaron partes del departamento intactas', 'Positiva'),
  ('Ordenar cuáles son los daños urgentes y cuáles conviene resolver más adelante en la vivienda', 'Competente'),
  ('No saltar enseguida a soluciones sin registrar la dimensión de lo que la tormenta arruinó', 'Reactiva')]),

# arm1 11 — amenaza · recuperar esperanza / próximo paso / no cerrar demasiado rápido
("N", "arm1 11",
 'Cuando un vecino te cuenta que lo echaron del trabajo, lo que más te pesa es:', "scenario",
 [('Que además del trabajo se le venga abajo todo lo que venía armando', 'Positiva'),
  ('Verlo sin la menor idea de por dónde arrancar mañana', 'Competente'),
  ('Escuchar que le digan enseguida que algo mejor va a aparecer', 'Reactiva')]),

# arm1 12 — amenaza · conservar vínculo o estabilidad / separar reacción de resolución / no fingir que nada pasó
("N", "arm1 12",
 'Cuando en una juntada dos amigos se pelean fuerte y el ambiente queda tenso, lo que menos tolerarías es:', "scenario",
 [('Que una pelea de dos arruine el grupo entero', 'Positiva'),
  ('Que se queden en el ida y vuelta sin ir al fondo del asunto', 'Competente'),
  ('Que se cambie de tema y se siga como si nada', 'Reactiva')]),

# arm1 14 — amenaza · algo que siga teniendo valor / corregir / reconocer gravedad
("N", "arm1 14",
 'Cuando descubrís que un error de hace meses en tu trabajo perjudicó a otro y todavía tiene consecuencias, lo que más te gustaría es:', "scenario",
 [('Conservar la confianza que había antes de esto', 'Positiva'),
  ('Que se corrija lo que todavía se puede arreglar', 'Competente'),
  ('Reconocer lo que el otro tuvo que aguantar por ese error', 'Reactiva')]),

# arm1 15 — amenaza · preservar lo bueno / definir el problema / no minimizar
("N", "arm1 15",
 'Cuando un proveedor atrasa varias entregas y el proyecto del que sos parte se corre de fecha, lo primero que mirás es:', "scenario",
 [('Todo lo que ya habían hecho bien y no se perdió', 'Positiva'),
  ('Saber si el problema es el proveedor o cómo está armado el plan', 'Competente'),
  ('Ver que el atraso ya no le llama la atención a nadie', 'Reactiva')]),

# arm1 16 — amenaza · impedir que lo malo contamine todo / estructurar / nombrar lo ocurrido
("N", "arm1 16",
 'Cuando en tu casa hace meses que la plata no alcanza para cubrir todos los gastos, lo que más te gustaría es:', "scenario",
 [('Volver a hablar de otra cosa además de la plata', 'Positiva'),
  ('Tener por fin una cuenta clara de en qué se va', 'Competente'),
  ('Decir con todas las letras cómo estamos', 'Reactiva')]),


# ---------------------------------------------------------------------------
# Lote 2 de Armónico, 7 filas. Con esto el conjunto cierra sus 24 de escenario.
# Fuente: [[Lote Armónico 2 — Adjudicación y correcciones]]
# Spec:   [[Spec de Conjunto — Armónico (v3, correcciones de lenguaje)]]
#
# Primer lote escrito bajo la regla 15 (nunca reescribir para evitar el «Que» inicial). El
# revisor confirmó que las aperturas repetidas pasan completamente desapercibidas.
# Adjudicación: 6 filas completas a Claude, 1 mixta, ninguna a ChatGPT.

# arm2 03 — amenaza · preservar lo bueno / próximo paso / no minimizar
("N", "arm2 03",
 'Cuando elegiste vos el alojamiento del viaje y resulta mucho peor de lo que mostraban las fotos, lo primero que mirás es:', "scenario",
 [('Que el viaje no se arruine por dónde están durmiendo', 'Positiva'),
  ('Si conviene quedarse o salir a buscar otro lugar hoy mismo', 'Competente'),
  ('Que no se convierta enseguida en chiste lo que en serio está mal', 'Reactiva')]),

# arm2 04 — amenaza · algo que siga teniendo valor / definir el problema / reconocer gravedad
("N", "arm2 04",
 'Cuando te das cuenta de que hace rato venís dejando de lado a un grupo de amigos, lo que más te cuesta es:', "scenario",
 [('Sostener que ese grupo todavía tiene algo bueno para vos', 'Positiva'),
  ('Ubicar en qué momento dejaste de estar y por qué', 'Competente'),
  ('Aceptar que no fue un bache sino que se fue cortando', 'Reactiva')]),

# arm2 08 — amenaza · impedir que lo malo contamine todo / próximo paso / dar espacio a lo difícil
("N", "arm2 08",
 'Cuando la computadora con la que estudiás deja de andar en plena semana de entregas, lo primero que necesitás es:', "scenario",
 [('Mentalizarte en que la falla de la computadora no convierta la semana entera en un desastre', 'Positiva'),
  ('Tener resuelto con qué seguir antes de que termine el día', 'Competente'),
  ('Registrar el golpe un minuto antes de ponerte a resolver', 'Reactiva')]),

# arm2 09 — amenaza · preservar lo bueno / entender / dar espacio a lo difícil
("N", "arm2 09",
 'Cuando a un amigo le cambian dos veces la fecha de la mudanza y no sabe cuándo puede entrar, lo que te sale es:', "scenario",
 [('Señalarle que lo que se atrasó es la fecha, no la mudanza', 'Positiva'),
  ('Ver con él de qué depende que se destrabe', 'Competente'),
  ('Que pueda decir lo insoportable que es sin que le bajen el tono', 'Reactiva')]),

# arm2 13 — amenaza · recuperar perspectiva / estructurar / nombrar lo ocurrido
("N", "arm2 13",
 'Cuando en un asado familiar alguien hace un comentario que deja incómodos a todos, lo que más te importa es:', "scenario",
 [('Que un comentario no arruine toda la reunión y se pueda seguir compartiendo', 'Positiva'),
  ('Distinguir qué fue exactamente lo que incomodó y si hace falta decir algo', 'Competente'),
  ('Que quede dicho que estuvo de más, aunque sea después', 'Reactiva')]),

# arm2 17 — amenaza · recuperar esperanza / separar reacción de resolución / no cerrar demasiado rápido
("N", "arm2 17",
 'Cuando en una actividad que organiza tu grupo se cancela a último momento el lugar que habían reservado, lo que más te cuesta es:', "scenario",
 [('Volver a creer que la actividad igual va a salir', 'Positiva'),
  ('Que el enojo del momento no tape que hay que conseguir otro lugar', 'Competente'),
  ('Que se pase a resolver sin que nadie diga lo que costó armarlo', 'Reactiva')]),

# arm2 18 — amenaza · recordar recursos / estructurar / no fingir que nada pasó
("N", "arm2 18",
 'Cuando el emprendimiento que armaron entre varios hace meses que no levanta, lo que más te ayuda es:', "scenario",
 [('Acordarte de lo que sí saben hacer bien entre todos', 'Positiva'),
  ('Mirar con números en qué parte no está cerrando', 'Competente'),
  ('Que se diga que hace meses no levanta y no que es cuestión de tiempo', 'Reactiva')]),

# --- Likert de Armónico (12) — cierra el conjunto -------------------------
# Fuente: [[Lote Armónico Likert — Adjudicación y correcciones]].
# Spec:   [[Spec de Ítems Likert — Armónico (v2, post-auditoría)]].
# 7 de 12 sin ganador en la comparación: ninguna de las dos versiones metía la
# situación adentro de la frase. El set final lleva 6 reescrituras del revisor.
# Sin inversas: ningún grupo de Armónico admite una limpia (regla 7b endurecida).

("N", "alik 31 · recordar recursos",
 "Cuando se me cae un plan que esperaba hace semanas, me sale acordarme enseguida de la gente y las ganas que igual siguen estando",
 "likert", "Positiva"),

("N", "alik 32 · conservar vínculo o estabilidad",
 "Después de dos semanas discutiendo lo mismo con mi pareja, me pesa que la pelea empiece a definir toda la relación",
 "likert", "Positiva"),

("N", "alik 33 · recuperar perspectiva",
 "Si me preguntan por el proyecto al que le dediqué dos años y que la empresa canceló, termino contándolo como una etapa que valió y no como dos años perdidos",
 "likert", "Positiva"),

("N", "alik 34 · recuperar esperanza",
 "Cuando un amigo me cuenta por tercera vez que su búsqueda de trabajo no avanza, prefiero sostener que algo va a aparecer, sin tener con qué probarlo, antes que darle la razón",
 "likert", "Positiva"),

("N", "alik 35 · separar reacción de resolución",
 "En el chat del consorcio, me impacienta que los reproches ocupen más espacio que decidir qué hacer con el presupuesto",
 "likert", "Competente"),

("N", "alik 36 · ordenar",
 "Si en una semana se me junta una entrega, una canilla rota y una visita familiar para reorganizar, me siento trabado hasta ponerles un orden",
 "likert", "Competente"),

("N", "alik 37 · definir el problema",
 "Una planilla de gastos que armé empieza a dar totales distintos, y no me sale seguir usándola hasta ubicar en qué paso aparece la diferencia, aunque me lleve toda la tarde",
 "likert", "Competente"),

("N", "alik 38 · corregir",
 "Veo que un compañero mandó un informe con una cifra equivocada que cambia una comparación secundaria, no la conclusión; antes de medir cómo se lo digo, me gana la necesidad de que esa cifra quede corregida",
 "likert", "Competente"),

("N", "alik 39 · no fingir que nada pasó",
 "Vuelvo a reunirme con el equipo meses después de que otra área canceló un proyecto que habíamos preparado entre todos, y me cuesta arrancar sin que se diga primero lo que perdimos",
 "likert", "Reactiva"),

("N", "alik 40 · no cerrar demasiado rápido",
 "No termino de pasar a otra cosa el mismo día que me avisan que no quedé en algo que preparé durante meses",
 "likert", "Reactiva"),

("N", "alik 41 · dar espacio a lo difícil",
 "Cuando alguien de mi familia está pasando una separación difícil y el tema vuelve en cada encuentro, me quedo conversándolo todo lo que haga falta antes de llevar la charla a otro lado, aunque se ponga pesado",
 "likert", "Reactiva"),

("N", "alik 42 · nombrar lo ocurrido",
 "Pasaron años desde la mudanza que debimos hacer de golpe porque el propietario no renovó, pero cada vez que vuelve el tema sigo necesitando poner en palabras lo abrupto que fue, aunque los demás ya lo tengan escuchado",
 "likert", "Reactiva"),
]
