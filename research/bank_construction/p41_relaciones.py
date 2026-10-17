# -*- coding: utf-8 -*-
"""Prototype v4.1 — Conjunto de Relaciones Objetales (6 items).

Source: [[NureonAI Prototype v4.1 — Transcribed Corrections]].
R4 Rechazo ("Que fuiste una carga") is the shortest option in the set at exactly
4 words, which is why the floor was lowered from 6 to 4.
"""
from relaciones import SYSTEM, GROUPS, GROUP_TYPES  # noqa: F401

ITEMS = [
("N", "v4.1 R1",
 "Lo que más te costaría perdonarle a alguien cercano sería:", "scenario",
 [("Que haya cambiado por completo la relación sin darte chance de ubicarte en ese nuevo lugar", "Apego"),
  ("Que haya arruinado algo que podía haber sido muy bueno", "Frustración"),
  ("Que dé por hecho lo que aportás y sólo cuente con vos por eso", "Rechazo")]),

("N", "v4.1 R2",
 "Lo que más te haría sentir que perdiste años de tu vida sería:", "scenario",
 [("Haberte amoldado tanto a lo que había que terminaste perdiendo de vista lo que querías vos", "Apego"),
  ("Haberte conformado con mucho menos de lo que estabas buscando", "Frustración"),
  ("Haber terminado necesitando de otros después de acostumbrarte a ser vos quien tenía algo para aportar", "Rechazo")]),

("N", "v4.1 R3",
 "En un vínculo importante, lo que más buscás es:", "scenario",
 [("Que se sostenga en el tiempo y seguir sabiendo cuál es tu lugar", "Apego"),
  ("Que llegue a ser el vínculo que sentís que podría ser", "Frustración"),
  ("Poder aportar lo tuyo sin sentir que terminás siendo vos quien más necesita del otro", "Rechazo")]),

("N", "v4.1 R4",
 "Lo que más te dolería escuchar de alguien importante para vos sería:", "scenario",
 [("Que ya no hay lugar para vos en su vida", "Apego"),
  ("Que al final terminaste con algo muy por debajo de lo que imaginabas que podía ser", "Frustración"),
  ("Que fuiste una carga", "Rechazo")]),

("N", "v4.1 R5",
 "Cuando conocés a alguien que te interesa, lo que más te importa es:", "scenario",
 [("Que se vaya armando algo donde sientas que tenés un lugar y pueda sostenerse en el tiempo", "Apego"),
  ("Sentir que puede llegar a ser el tipo de vínculo que realmente buscás", "Frustración"),
  ("Sentir que vos también tenés algo para aportar y no sólo cosas para pedir", "Rechazo")]),

("N", "v4.1 R6",
 "En una discusión con tu pareja o un amigo cercano, lo que más te importa es:", "scenario",
 [("Que puedan volver a encontrar un lugar claro entre ustedes después de la discusión", "Apego"),
  ("Aprovechar la discusión para que el vínculo quede mejor que antes", "Frustración"),
  ("No quedar como una persona que sólo pide y dejar en claro que también podés aportar algo a la relación", "Rechazo")]),

# --- Lote 1 de Relaciones (12 escenarios) ---------------------------------
# Fuente: [[Lote Relaciones 1 — Adjudicación y correcciones]].
# Spec:   [[Spec de Conjunto — Relaciones Objetales (v2, post-auditoría)]].
# ChatGPT 7 filas, Claude 3, dos mixtas; R5 entera y dos Frustraciones son de Tobías.

("N", "rel1 01",
 "Cuando entrás a un grupo donde ya todos se conocen de antes, lo que más te importa al principio es:", "scenario",
 [("Captar cómo funciona el grupo para ubicarte dentro de eso", "Apego"),
  ("Que el grupo resulte estar a la altura de lo que parecía desde afuera", "Frustración"),
  ("Que el vínculo con ellos no termine girando sólo alrededor de para qué servís", "Rechazo")]),

("N", "rel1 02",
 "Cuando empezás a trabajar con alguien que sabe mucho más que vos, lo que más te ocupa es:", "scenario",
 [("Ir armando de qué te vas a encargar vos dentro de ese trabajo", "Apego"),
  ("Que trabajar con alguien así pueda dar mucho más de lo que está dando", "Frustración"),
  ("Tener algo tuyo para poner en ese trabajo y no sólo cosas para preguntar", "Rechazo")]),

("N", "rel1 04",
 "Cuando en tu pareja tienen que decidir dónde pasar las fiestas y las dos familias esperan, lo que más te cuesta de eso es:", "scenario",
 [("Que las costumbres de ambas familias ya vengan armadas y tengas que encontrar cómo moverte entre ellas", "Apego"),
  ("Llegar a un acuerdo con lo primero que cierre a ambas, cuando podría haber sido mucho mejor", "Frustración"),
  ("Que entre lo que quieren las dos familias, lo que vos querés termine quedando último", "Rechazo")]),

("N", "rel1 05",
 "Cuando un amigo te pide ayuda por tercera vez en el mes, lo que más te pesa es:", "scenario",
 [("Que tengas que replantearte qué te hace parte de esa amistad", "Apego"),
  ("Que una amistad de años quede reducida a estos pedidos sin la reciprocidad que esperabas", "Frustración"),
  ("Tomar la posición de quien resuelve y que no pueda cambiarse", "Rechazo")]),

("N", "rel1 07",
 "Cuando tenés un compañero de trabajo con el que te entendés muy bien, lo que más te importa de eso es:", "scenario",
 [("Poder contar con una forma de trabajar juntos que ya sabés cómo funciona entre ustedes", "Apego"),
  ("Que una sintonía tan buena no quede sólo en llevarse bien y pueda convertirse en una colaboración más rica", "Frustración"),
  ("Disfrutar esa sintonía sin quedar siempre como el que resuelve o sostiene cuando aparece una dificultad", "Rechazo")]),

("N", "rel1 09",
 "Cuando tu pareja te dice que necesita más tiempo para sus cosas, lo primero que se te viene es:", "scenario",
 [("Qué cambia para vos en la relación ahora que van a compartir menos tiempo", "Apego"),
  ("La distancia entre este nuevo arreglo y la forma de pareja que para vos tendría más sentido", "Frustración"),
  ("Que el nuevo arreglo tenga muy en cuenta lo que necesita tu pareja y deje casi afuera lo tuyo", "Rechazo")]),

("N", "rel1 11",
 "Cuando en tu familia quedaste en el medio de dos personas que no se hablan, lo que más te pesa es:", "scenario",
 [("Quedar metido entre dos personas sin encontrar cómo relacionarte con cada una sin seguir en el medio", "Apego"),
  ("Que la relación entre ellos siga alrededor del conflicto, cuando podría existir una forma menos quebrada de vincularse", "Frustración"),
  ("Que cada conversación termine pasando por vos porque sos quien todavía puede sostener el intercambio entre los dos", "Rechazo")]),

("N", "rel1 13",
 "Si el grupo del que formás parte decide cambiar por completo para qué se reúne, lo que más te dolería es:", "scenario",
 [("Que las reglas implícitas con las que venías participando dejen de servir dentro del grupo", "Apego"),
  ("Ver que el grupo se aleja de la versión que para vos justificaba seguir formando parte", "Frustración"),
  ("Que termines en una posición útil para la nueva etapa, pero tus propias necesidades queden afuera", "Rechazo")]),

("N", "rel1 15",
 "Cuando alguien de tu familia con quien te habías peleado te escribe después de meses, lo primero que se te viene es:", "scenario",
 [("Cómo volver a relacionarte con esa persona a partir de lo que efectivamente te escribió, no de cómo era antes", "Apego"),
  ("Lo que tendría que cambiar entre ustedes para que retomar el contacto no sea volver a la misma relación", "Frustración"),
  ("Que retomar el contacto vuelva a dejarte del lado de quien sostiene la relación cuando aparece tensión", "Rechazo")]),

("N", "rel1 16",
 "Cuando volvés a un trabajo donde ya habías estado hace años, lo que más te ocupa es:", "scenario",
 [("Ver qué de lo que sabías de antes todavía te sirve para manejarte", "Apego"),
  ("Que esta segunda vez termine dando lo mismo que la primera, cuando podía dar más", "Frustración"),
  ("Volver con algo más para dar de lo que traías la primera vez", "Rechazo")]),

("N", "rel1 17",
 "Cuando en un curso de un día te toca hacer una actividad de a dos con alguien que no conocés, lo que más te cuesta es:", "scenario",
 [("Tardar en agarrarle la mano a cómo se van a repartir las cosas", "Apego"),
  ("Que la dinámica real se aleje bastante de cómo imaginabas trabajar con alguien en ese curso", "Frustración"),
  ("Que durante la actividad tengas que pedirle ayuda varias veces sin poder devolverle nada útil en ese intercambio", "Rechazo")]),

("N", "rel1 18",
 "Cuando en tu grupo empiezan a rotar quién coordina cada encuentro, lo que más te importa de eso es:", "scenario",
 [("Tener claro cómo quedás ubicado cuando coordina otra persona y qué cambia cuando coordinás vos", "Apego"),
  ("Que la rotación no se vuelva automática si para vos hay formas de coordinar que podrían funcionar mejor", "Frustración"),
  ("Que aunque coordine otro, el encuentro igual tenga algo puesto por vos", "Rechazo")]),

# --- Lote 2 de Relaciones (6 escenarios) — cierra los 24 del conjunto -------
# Fuente: [[Lote Relaciones 2 — Adjudicación y correcciones]].
# R3 se rehizo entera; R6/R8/R10 son mixtas; R12 y R14 son de Claude.

("N", "rel2 03",
 "Cuando una amistad nueva empieza a volverse importante para vos, lo que más te importa al principio es:", "scenario",
 [("Que se vaya asentando y vos sepas qué son el uno para el otro", "Apego"),
  ("Que se quede en lo que ya comparten justo cuando estaba creciendo", "Frustración"),
  ("Estar siempre ofreciendo y todavía no haberle pedido nada", "Rechazo")]),

("N", "rel2 06",
 "Cuando en tu familia están preparando un festejo grande y todavía no repartieron quién se ocupa de qué, lo que más te condiciona es:", "scenario",
 [("Que el reparto no esté hecho y todavía no sepas cuál va a ser tu parte", "Apego"),
  ("Que se reparta como todos los años, cuando esta familia podría organizarse mucho mejor", "Frustración"),
  ("Quedar sólo esperando qué te asignan, sin poder aportar como te gustaría", "Rechazo")]),

("N", "rel2 08",
 "Cuando en el edificio donde vivís empiezan a turnarse para recibir paquetes y vos sos el que más días está en casa, lo que más te llama la atención es:", "scenario",
 [("Que la dinámica se arme según los horarios disponibles de cada uno y tengas que encontrar cómo acomodarte", "Apego"),
  ("Que el turno se cumpla y a nadie termine sirviéndole de verdad", "Frustración"),
  ("Que estar más en casa te vaya dejando a cargo de los paquetes de todos", "Rechazo")]),

("N", "rel2 10",
 "Cuando un amigo de años te empieza a contestar cada vez menos, lo que más te cuesta es:", "scenario",
 [("Tener que acostumbrarte a una relación con menos contacto y saber cómo tratar ahora a esa persona", "Apego"),
  ("Que acostumbrarte a menos contacto sea resignar la cercanía que todavía querías", "Frustración"),
  ("Tener que ser vos el que escribe primero cada vez para sostener el contacto", "Rechazo")]),

("N", "rel2 12",
 "Cuando una amiga con la que te veías todas las semanas se muda a otra provincia, lo que más te quedaría dando vueltas es:", "scenario",
 [("Si esa amistad va a seguir existiendo a la distancia y de qué forma", "Apego"),
  ("Todo lo que esa amistad tenía por delante y ya no va a pasar", "Frustración"),
  ("Que verse pase a depender de que vos lo pidas", "Rechazo")]),

("N", "rel2 14",
 "Cuando termina una relación y hay que repartir lo que era de los dos, lo que más te cuesta de eso es:", "scenario",
 [("Darte cuenta de cuánto de lo que armaron era lo que quería el otro", "Apego"),
  ("Repartir rápido para terminar con el trámite, cuando la relación merecía un cierre mejor", "Frustración"),
  ("Ceder las cosas que te importaban para que el otro salga entero", "Rechazo")]),

# --- Likert de Relaciones Objetales (12) — cierra el conjunto y la fase A ---
# Fuente: [[Lote Relaciones Likert — Adjudicación y correcciones]].
# Spec:   [[Spec de Ítems Likert — Relaciones Objetales (v2, post-auditoría)]].
# 44 va en las DOS polaridades: es el par de control de la regla 7b endurecida.
#   directa {3,6,9} acuerdan · inversa {1,4,5,7,8} acuerdan, ningún miembro de Apego.
# 43 y 54 se reescribieron por defectos de contrato, no de prosa (ver nota §3 y §4).

("N", "rlik 43 · conservar un lugar",
 "Suman a alguien al equipo y vuelven a repartir las tareas que estaban fijas, y me pesa más quedarme sin una parte clara que perder la que tenía",
 "likert", "Apego"),

("N", "rlik 44d · saber dónde estás parado",
 "Si una amiga con la que hablo seguido empieza a responderme mucho más corto varios días, enseguida necesito ubicar cómo quedamos entre nosotros",
 "likert", "Apego"),

("N", "rlik 44i · saber dónde estás parado",
 "Cuando una amiga con la que hablo seguido empieza a contestarme mucho más corto varios días seguidos, lo tomo como que está en otra y sigo con lo mío",
 "likert", ("Apego", "inversa")),

("N", "rlik 45 · perder el deseo propio por acomodación",
 "Si mi pareja propone aprovechar una oferta a un destino que no era el que yo tenía pensado, me sumo enseguida y recién en el viaje me doy cuenta de lo que quería",
 "likert", "Apego"),

("N", "rlik 46 · pertenencia",
 "En una comida familiar proponen repetir una tradición que empezó antes de que yo fuera, y prefiero sumarme igual antes que quedar mirando desde afuera",
 "likert", "Apego"),

("N", "rlik 47 · potencial no realizado",
 "Cuando un amigo con el que armábamos proyectos importantes lleva un tiempo escribiéndome sólo sobre cosas del día a día, me pesa pensar cuánto se desvió de lo que esa amistad podía ser",
 "likert", "Frustración"),

("N", "rlik 48 · no conformarse",
 "Un amigo nos dice que tenemos la convivencia muy bien resuelta, y me queda dando vueltas todo lo que igual nos estamos perdiendo",
 "likert", "Frustración"),

("N", "rlik 49 · ideal vs realidad",
 "En el grupo con el que cenamos una vez por mes proponen seguir igual el año que viene, y a mí no se me ocurre qué podría faltarle",
 "likert", ("Frustración", "inversa")),

("N", "rlik 50 · reparar hacia una forma más ideal",
 "Al retomar contacto con un hermano después de meses sin hablarnos, me importa más que cambie nuestra forma de vincularnos que simplemente volver a hablar",
 "likert", "Frustración"),

("N", "rlik 51 · tener algo propio para ofrecer",
 "Arman en el edificio una actividad para que se conozcan los vecinos, y me cuesta sumarme si no tengo con qué contribuir",
 "likert", "Rechazo"),

("N", "rlik 52 · invertir la posición de proveedor",
 "Una operación menor me deja unas semanas necesitando que me lleven y me traigan, y me cuesta más pedirlo que atravesar la operación, porque siempre fui yo el que llevaba y ahora quedo del lado de necesitar",
 "likert", "Rechazo"),

("N", "rlik 53 · incomodidad al quedar del lado de pedir",
 "Si estoy con una semana cargada y un amigo se ofrece a dejarme comida, me resulta natural aceptar el cuidado sin compensarlo enseguida",
 "likert", ("Rechazo", "inversa")),

("N", "rlik 54 · ser quien sostiene",
 "Cuando mi pareja lleva meses buscando trabajo y esta semana le vuelven a decir que no, prefiero cargar yo con más cosas antes que quedarme sin nada para darle",
 "likert", "Rechazo"),
]
