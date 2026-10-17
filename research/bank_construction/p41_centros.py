# -*- coding: utf-8 -*-
"""Prototype v4.1 — Centros de Inteligencia (6 items).

Source: [[NureonAI Prototype v4.1 — Transcribed Corrections]].
SYSTEM / GROUPS / GROUP_TYPES are imported from the bank module so the
prototype can never drift from the bank's group and type definitions.
"""
from centros import SYSTEM, GROUPS, GROUP_TYPES  # noqa: F401

ITEMS = [
("N", "v4.1 C1",
 "Después de un año difícil, lo que más te pesa es:", "scenario",
 [("La tensión y el enojo que se te fueron acumulando en el cuerpo", "Cuerpo"),
  ("Sentir que la gente que te importa no llegó a ver realmente lo que viviste", "Corazón"),
  ("Haber pasado tanto tiempo sin encontrar con qué orientarte ni saber cómo moverte frente a lo que iba apareciendo", "Mente")]),

("N", "v4.1 C2",
 "Si tuvieras que empezar de cero en un lugar desconocido, lo peor sería:", "scenario",
 [("No poder encontrar tu propio lugar ni manejarte según lo que te sale naturalmente", "Cuerpo"),
  ("Tener que empezar de cero también con lo que los demás saben de vos", "Corazón"),
  ("No saber todavía cómo funcionan las cosas ahí", "Mente")]),

("N", "v4.1 C3",
 "Después de una discusión fuerte con tu familia, lo que más te sigue afectando es:", "scenario",
 [("La tensión que se te queda acumulada en el cuerpo", "Cuerpo"),
  # Regla 10 (concreción): la version anterior — "Haber quedado ante ellos como
  # alguien que no sos" — era una inferencia sobre lo que piensan los otros,
  # mientras Cuerpo y Mente son cosas que el respondente sabe de si mismo.
  # "Sentir que" devuelve el juicio adentro del respondente.
  ("Sentir que quedaste ante ellos como alguien que no sos", "Corazón"),
  ("No saber en qué quedó todo ni qué esperar ahora", "Mente")]),

("N", "v4.1 C4",
 "Lo que más te costaría de un trabajo que tomaste sin poder elegirlo sería:", "scenario",
 [("Tener que manejarte todo el tiempo de una forma que sentís ajena a vos", "Cuerpo"),
  ("Sentir que no hay forma de mostrar quién sos ni lo que valés", "Corazón"),
  ("No tener con qué orientarte cuando cambian las cosas o toman decisiones nuevas", "Mente")]),

("N", "v4.1 C5",
 "Cuando algo importante depende de otra persona, lo que más te cuesta es:", "scenario",
 [("La tensión de no poder hacer nada desde tu lugar hasta que el otro se mueva", "Cuerpo"),
  ("Quedarte sin saber si lo que esto significa para vos llegó a contar en su decisión", "Corazón"),
  ("No poder ubicar qué puede pasar ni qué opciones te quedarían después", "Mente")]),

("N", "v4.1 C6",
 "Si tuvieras que aguantar la misma situación durante años, lo que más te costaría sería:", "scenario",
 [("Convivir todos los días con algo que por dentro sentís que no está bien", "Cuerpo"),
  ("Que a los que tenés cerca les dé igual quién sos", "Corazón"),
  ("No saber nunca a qué atenerte con lo que pueda venir", "Mente")]),

# ---------------------------------------------------------------------------
# Lote 1 — [[Lote 1 Centros — Set consolidado]], aprobado 2026-09-07.
# Salido de redacción ciega en paralelo (ChatGPT / Claude) sobre el spec
# [[Spec de Facetas — Centros lote 2 (v2, post-revisión)]], adjudicado a ciegas.
# ---------------------------------------------------------------------------

("N", "lote1 01",
 "Después de una entrega importante que salió mal, lo que peor te queda es:", "scenario",
 [("Quedarte con el cuerpo acelerado un buen rato después", "Cuerpo"),
  ("Quedarte con la sensación de que nada de lo que pusiste valió", "Corazón"),
  ("No terminar de entender en qué momento se te fue de las manos", "Mente")]),

("N", "lote1 02",
 "Después de varios meses con la plata ajustada, lo que menos tolerarías es:", "scenario",
 [("Sentir que tenés que vivir durante meses a un ritmo que te desgasta", "Cuerpo"),
  ("Sentir que tu esfuerzo deja de parecerte suficiente, aunque estés haciendo todo lo que podés", "Corazón"),
  ("Pasar meses sintiendo que nunca llegás suficientemente preparado para un gasto extra", "Mente")]),

("N", "lote1 03",
 "Cuando un amigo cambió mucho, lo que más te cuesta es:", "scenario",
 [("Sentir por dentro que algo en esa relación ya no te cierra", "Cuerpo"),
  ("Sentir que empezás a cuidar demasiado cómo quedás cuando hablás con esa persona", "Corazón"),
  ("Quedarte sin las referencias con las que antes entendías a esa persona", "Mente")]),

("N", "lote1 04",
 "Si tuvieras que convivir con gente que no elegiste, lo que más te costaría es:", "scenario",
 [("No llegar a encontrar una forma propia de desenvolverte dentro de esa casa", "Cuerpo"),
  ("Sentir que te vas acomodando tanto que dejás de reconocerte en cómo actuás", "Corazón"),
  ("No terminar de armar un mapa claro de cómo funciona esa convivencia", "Mente")]),

("N", "lote1 05",
 "Frente a una decisión que no podés seguir postergando, lo que más te traba es:", "scenario",
 [("Que por dentro ninguna te termine de cerrar del todo", "Cuerpo"),
  ("No poder reconocer qué elección te representa más de verdad", "Corazón"),
  ("No poder ver con claridad qué posibilidades reales abre cada opción", "Mente")]),

("N", "lote1 06",
 "Si tuvieras que volver a vivir a la casa de tu familia, lo que más te pesaría es:", "scenario",
 [("Pensar en volver y ya sentir el cuerpo rígido por esa convivencia", "Cuerpo"),
  ("Imaginarte cayendo otra vez en una versión de vos que ya no querés mostrar", "Corazón"),
  ("Que tus referencias vuelvan a ser las de ellos y no las tuyas", "Mente")]),

("N", "lote1 07",
 "Si tuvieras que elegir entre dos oportunidades que te atraen por igual, lo que más te ayudaría a decidir es:", "scenario",
 [("Sentir cuál de las dos podrías sostener sin ir contra tus propios límites", "Cuerpo"),
  ("Reconocer en cuál de las dos te ves más reflejado", "Corazón"),
  ("Ver cuál de las dos te abre posibilidades que realmente te interesan", "Mente")]),

("N", "lote1 08",
 "Cuando te sale muy bien algo que te importaba, lo primero que sentís es:", "scenario",
 [("Toda la tensión que venías cargando soltándose de golpe", "Cuerpo"),
  ("Sentir que todo lo que pusiste por fin contó de verdad", "Corazón"),
  ("Empezar a ver enseguida todo lo que ahora se vuelve posible", "Mente")]),

("N", "lote1 09",
 "Si algo importante para vos tuviera que frenarse varios meses por una circunstancia externa, lo que más se te haría cuesta arriba es:", "scenario",
 [("Perder un ritmo que te había costado mucho tomar", "Cuerpo"),
  ("Sentir que una parte importante de vos queda en pausa todo ese tiempo", "Corazón"),
  ("Que todo lo que ya tenías preparado quede sin poder usarse", "Mente")]),

("N", "lote1 10",
 "Cuando estás por meterte en un proyecto que te va a ocupar varios meses, lo que necesitás antes de arrancar es:", "scenario",
 [("Que la decisión te resulte firme por dentro antes de comprometerte", "Cuerpo"),
  ("Sentir que ese proyecto tiene suficiente valor para vos como para involucrarte", "Corazón"),
  ("Entender bien en qué te estás metiendo y qué se te abre si lo hacés", "Mente")]),

("N", "lote1 11",
 "Cuando organizás algo que querés que salga bien, lo que más te importa cuidar es:", "scenario",
 [("No exigirte más de lo que sabés que podés sostener sin pasarte", "Cuerpo"),
  ("Que el resultado muestre una versión de vos con la que te sientas cómodo", "Corazón"),
  ("Que haya más de una forma posible de seguir si algo se complica", "Mente")]),

("N", "lote1 12",
 "Cuando algo que venías haciendo se termina antes de lo esperado, lo que más te cuesta soltar es:", "scenario",
 [("Seguir con el cuerpo puesto en algo que ya se terminó", "Cuerpo"),
  ("Perder algo que ya sentías como parte de lo que sos", "Corazón"),
  ("Todos los planes que ya tenías armados y ahora no van a pasar", "Mente")]),

# ---------------------------------------------------------------------------
# Lote Likert 1 — [[Lote Likert Centros — Resultado y set consolidado]],
# aprobado 2026-09-08. Redacción ciega en paralelo, adjudicada sin atribución.
# 4 por grupo · 3 inversas (25%), una por grupo.
# ---------------------------------------------------------------------------

("N", "likert1 01 · tensión/residuo",
 "Después de discutir con alguien y terminar en buenos términos, noto que la tensión me sigue acompañando físicamente",
 "likert", "Cuerpo"),
("N", "likert1 02 · límites sentidos",
 "Mientras espero en una fila, noto una incomodidad física cuando la persona de atrás se me va acercando demasiado",
 "likert", "Cuerpo"),
("N", "likert1 03 · ritmo propio",
 "Cuando la entrega de un trabajo grupal se adelanta una semana, sigo el ritmo nuevo aunque siento que estoy forzando mi propio paso",
 "likert", "Cuerpo"),
("N", "likert1 04 · resistencia interna · agreement {3,5,7,9}",
 "En un viaje largo en micro, con un asiento incómodo y varias horas de viaje por delante, me acomodo como puedo y el malestar pasa a un segundo plano",
 "likert", ("Cuerpo", "inversa")),
("N", "likert1 05 · reconocimiento",
 "Cuando en una reunión aparece un resultado del equipo con una parte a la que le dediqué bastante, me pesa que mi contribución se vuelva indistinguible",
 "likert", "Corazón"),
("N", "likert1 06 · valor personal",
 "Si me ofrecen trabajar en un proyecto bien pago durante seis meses en un área que nunca elegí, me importa más sentir que tiene sentido para mí que la conveniencia del sueldo",
 "likert", "Corazón"),
("N", "likert1 07 · significado interpersonal",
 "Si un amigo cercano me invita a su fiesta con un mensaje común enviado en el grupo general, me afecta no recibir una señal más personal de cuánto significo para él",
 "likert", "Corazón"),
("N", "likert1 08 · discrepancia identidad/representación",
 "En un grupo nuevo, cuando alguien me presenta con una sola palabra, me queda dando vueltas la imagen que acaba de instalarse sobre mí",
 "likert", "Corazón"),
("N", "likert1 09 · referencias",
 "Cuando alguien con quien trabajo hace meses reacciona de una manera inesperada, me quedo sin saber cómo leerlo",
 "likert", "Mente"),
("N", "likert1 10 · escenarios",
 "Si un amigo me propone poner dinero juntos en algo, prefiero demorar la respuesta hasta haber recorrido mentalmente varios desenlaces posibles",
 "likert", "Mente"),
("N", "likert1 11 · comprensión",
 "Escuchando a un familiar relatar un problema con varios nombres y detalles de gente que no ubico, me inquieta no poder armar una versión coherente de lo ocurrido",
 "likert", "Mente"),
("N", "likert1 12 · posibilidades · agreement {2,3,8,9}",
 "Después de reservar un alojamiento para un viaje largo y enterarme de que había otras zonas posibles que me interesan, puedo seguir conforme con lo elegido sin volver a comparar",
 "likert", ("Mente", "inversa")),


# ---------------------------------------------------------------------------
# Lote mixto v4, filas 19-24.
# Fuente: [[Lote mixto v4 — Adjudicación y set consolidado]]
# Spec:   [[Spec de Lote Mixto — v4, post-auditoría del rediseño]]
#
# Tercer intento del lote: la v2 se descartó entera (doce dominios con un solo esquema) y la v3
# volvió NO-GO en auditoría. Los dominios de la v4 se aprobaron sin duplicaciones.
# Redacción ciega en paralelo, adjudicada 7-3-2 con dos filas mixtas.
# El comentario de cada ítem es valencia · facetas en orden de columna.

# C19 — aprox · criterio visceral / identidad / escenarios
("N", "centros3 19",
 'Cuando te mudás a una casa que elegiste vos, lo primero que notás es:', "scenario",
 [('Esa primera impresión de que la casa te cierra o no apenas empezás a habitarla', 'Cuerpo'),
  ('Cuánto te reconocés en la vida que empezás a construir desde esa mudanza', 'Corazón'),
  ('Las distintas formas en que imaginás que podría organizarse tu vida en esa casa', 'Mente')]),

# C20 — aprox · posición / imagen / preparación
("N", "centros3 20",
 'Cuando en el trabajo pasás de ocuparte de una parte a encargarte de una entrega completa, lo que más te ocupa es:', "scenario",
 [('Qué tan firme te sentís al pasar de una parte a responder por todo', 'Cuerpo'),
  ('La versión de vos que mostrás cuando te hacés cargo de algo más grande', 'Corazón'),
  ('Cuántas referencias y recursos necesitás reunir para hacerte cargo de todo', 'Mente')]),

# C21 — neutral · tensión / significado personal / orientación
("N", "centros3 21",
 'Cuando volvés de un viaje largo, lo que más te cambia es:', "scenario",
 [('Cómo volvés a andar tenso a los dos días', 'Cuerpo'),
  ('Lo que antes te importaba ya no pesa lo mismo', 'Corazón'),
  ('Tener que volver a ubicar en qué estabas antes de irte', 'Mente')]),

# C22 — aprox · activación corporal / valor / posibilidades
("N", "centros3 22",
 'Cuando estrenás una bicicleta que elegiste durante meses, lo primero que notás es:', "scenario",
 [('La energía que sentís apenas empezás a pedalear con la bicicleta que elegiste', 'Cuerpo'),
  ('Cuánto sentís que esa elección dice algo importante sobre lo que priorizaste durante meses', 'Corazón'),
  ('Todas las formas nuevas de usarla que empezás a imaginar apenas salís a andar', 'Mente')]),

# C23 — aprox · ritmo / reconocimiento / comprensión
("N", "centros3 23",
 'Cuando terminás de pagar la última cuota de una compra grande, lo que más te cambia es:', "scenario",
 [('Que tus meses dejen de girar alrededor de la fecha de ese pago', 'Cuerpo'),
  ('Empezar a contar como propio el esfuerzo que hiciste para llegar hasta la última cuota', 'Corazón'),
  ('Ver con más claridad cuánto te condicionaba ese pago dentro de tus cuentas de cada mes', 'Mente')]),

# C24 — neutral · límites / significado personal / opciones
("N", "centros3 24",
 'Cuando tenés que elegir un regalo importante para un amigo que cumple años, lo que más mirás es:', "scenario",
 [('Hasta dónde te sale buscar sin empezar a sentir que la elección te exige demasiado', 'Cuerpo'),
  ('Qué querés expresar con ese regalo sobre lo que esa amistad representa para vos', 'Corazón'),
  ('Cuántas alternativas necesitás comparar antes de quedarte tranquilo con una elección concreta', 'Mente')]),
]
