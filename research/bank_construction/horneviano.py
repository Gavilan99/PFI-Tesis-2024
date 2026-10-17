# -*- coding: utf-8 -*-
# Conjunto Horneviano — Asertiva / Complaciente / Retraída
SYSTEM = "Conjunto Horneviano"
GROUPS = ["Asertiva", "Complaciente", "Retraída"]
# Member types per group. Used by build.py to default and validate `type_coverage`.
GROUP_TYPES = {"Asertiva": [3, 7, 8], "Complaciente": [1, 2, 6], "Retraída": [4, 5, 9]}

ITEMS = [
("R", "Anexo C #1 — de respuesta conductual a estrategia para conseguir lo que se quiere",
 "Cuando tus ideas son cuestionadas, lo que hacés para que prosperen es:", "scenario",
 [("Sostenerlas con firmeza hasta que se impongan", "Asertiva"),
  ("Ajustarlas para que el resto las acompañe", "Complaciente"),
  ("Retirarte a revisarlas y volver cuando estén sólidas", "Retraída")]),

("R", "Anexo C #2 — apunta a qué hace con la sobrecarga, no a cómo se siente",
 "Cuando estás sobrepasado, tu manera de recuperar terreno es:", "scenario",
 [("Empujar más fuerte y salir hacia adelante", "Asertiva"),
  ("Apoyarte en alguien que te ordene el panorama", "Complaciente"),
  ("Cortar contacto un rato y recuperar energía solo", "Retraída")]),

("R", "Anexo C #3 — reencuadrado hacia el primer movimiento real",
 "Ante una tarea difícil que te asignaron, tu primer movimiento es:", "scenario",
 [("Arrancar y marcar vos el ritmo", "Asertiva"),
  ("Confirmar con alguien que vas por el camino correcto", "Complaciente"),
  ("Estudiarla a fondo antes de mover una ficha", "Retraída")]),

("R", "Anexo C #4 — de 'cómo expresás' a qué condiciona tu intervención",
 "En un debate importante, lo que define cuándo hablás es:", "scenario",
 [("Que tengas algo que decir y ganas de decirlo", "Asertiva"),
  ("Que el momento sea el adecuado para el grupo", "Complaciente"),
  ("Que lo que vayas a aportar valga realmente la pena", "Retraída")]),

("R", "Anexo C #5 — la opción asertiva original era desmedida ('hasta que me dé la razon')",
 "Cuando critican tu trabajo, lo que hacés con esa crítica es:", "scenario",
 [("Discutirla en el momento si te parece injusta", "Asertiva"),
  ("Tomarla y ajustar para cumplir con lo que se espera", "Complaciente"),
  ("Guardarla y procesarla en privado antes de responder", "Retraída")]),

("R", "Anexo C #6 — corrige 'Retrarme' y apunta al instinto inicial",
 "Ante un desacuerdo, tu instinto inicial es:", "scenario",
 [("Plantearlo de frente y resolverlo rapido", "Asertiva"),
  ("Buscar un punto medio que deje conforme a los dos", "Complaciente"),
  ("Tomar distancia y pensarlo antes de responder", "Retraída")]),

("R", "Anexo C #7 — de 'qué hacés' a qué necesitás para poder decidir",
 "Cuando dudás de una decisión, lo que necesitás para poder avanzar es:", "scenario",
 [("Decidir igual y hacerte cargo después", "Asertiva"),
  ("Que alguien de confianza te confirme que está bien", "Complaciente"),
  ("Tiempo a solas para llegar a tu propia conclusión", "Retraída")]),

("R", "Anexo C #8 — foco en dónde se pone la energía bajo riesgo alto",
 "En una situación de mucho riesgo, tu energía se va principalmente a:", "scenario",
 [("Ir al frente aunque no esté todo claro", "Asertiva"),
  ("Cumplir con lo que se espera de vos", "Complaciente"),
  ("Analizar el terreno antes de exponerte", "Retraída")]),

("R", "Anexo C #9 — el rol como preferencia, no como descripción",
 "En un equipo, el lugar donde rendís mejor es:", "scenario",
 [("Conduciendo y empujando el proyecto", "Asertiva"),
  ("Articulando para que todos estén alineados", "Complaciente"),
  ("Trabajando con autonomía en tu propia parte", "Retraída")]),

("R", "Anexo C #10 — de 'cómo decidís actuar' a qué priorizás en la tensión",
 "En medio de una discusión intensa, lo que priorizás es:", "scenario",
 [("Decir lo que pensás sin filtrarlo demasiado", "Asertiva"),
  ("Que la relación no se dañe", "Complaciente"),
  ("Salir de ahí antes de decir algo de lo que te arrepientas", "Retraída")]),

("R", "Anexo C #11 — la opción retraída original ('ideas creativas') no representaba al grupo",
 "Lo que más te motiva al trabajar en equipo es:", "scenario",
 [("Llevar al grupo hacia donde ves que hay que ir", "Asertiva"),
  ("Que el grupo funcione y nadie quede afuera", "Complaciente"),
  ("Poder aportar desde tu especialidad sin que te dirijan", "Retraída")]),

("R", "Anexo C #12 — la opción complaciente original mezclaba perfeccionismo con reconocimiento",
 "Si te ofrecen un rol más exigente, lo que te haría aceptarlo es:", "scenario",
 [("Las ganas de medirte con algo más grande", "Asertiva"),
  ("Que confíen en vos y no querer defraudar esa confianza", "Complaciente"),
  ("El interés de la tarea en sí, más alla del cargo", "Retraída")]),

("R", "Anexo C #13 — de 'qué motiva tus interacciones' a la posición que buscás ocupar",
 "En una situación social, la posición en la que te sentís más comodo es:", "scenario",
 [("Llevando la conversación", "Asertiva"),
  ("Asegurándote de que todos estén incluidos", "Complaciente"),
  ("Observando desde un costado, participando lo justo", "Retraída")]),

("R", "Anexo C #14 — de 'qué impulsa tus decisiones' a criterio de futuro",
 "Al pensar en tu futuro, lo que ordena tus decisiones es:", "scenario",
 [("Hasta dónde querés llegar", "Asertiva"),
  ("Los compromisos que ya asumiste con otros", "Complaciente"),
  ("Lo que descubrís cuando te tomás tiempo a solas", "Retraída")]),

("R", "Anexo C #15 — de comportamiento a necesidad dentro del vínculo",
 "En una relación cercana, lo que necesitás para estar bien es:", "scenario",
 [("Que se respete tu manera de hacer las cosas", "Asertiva"),
  ("Saber que estás cumpliendo con tu parte del vínculo", "Complaciente"),
  ("Conservar un espacio propio que no se negocie", "Retraída")]),

("N", "", "Cuando algo te parece injusto en un grupo, lo más probable es que:", "scenario",
 [("Lo digas aunque incomode", "Asertiva"),
  ("Busques como arreglarlo sin romper nada", "Complaciente"),
  ("Te lo guardes y tomes distancia del grupo", "Retraída")]),

("N", "", "Lo que más te cuesta pedir es:", "scenario",
 [("Ayuda, porque preferís resolverlo vos", "Asertiva"),
  ("Algo para vos, sin sentir que estás molestando", "Complaciente"),
  ("Tiempo o espacio, sin tener que justificarlo", "Retraída")]),

("N", "", "Frente a una autoridad con la que no estás de acuerdo, lo que hacés es:", "scenario",
 [("Plantear tu desacuerdo directamente", "Asertiva"),
  ("Buscar la forma de cumplir sin generar conflicto", "Complaciente"),
  ("Hacer lo tuyo a tu manera, sin discutirlo", "Retraída")]),

("N", "", "Lo que más te incomoda de una reunión social grande es:", "scenario",
 [("Tener que esperar tu turno para hablar", "Asertiva"),
  ("Que alguien quede excluido", "Complaciente"),
  ("La exposición constante, sin poder retirarte", "Retraída")]),

("N", "", "Cuando alguien te pide un favor que no querés hacer, lo típico en vos es:", "scenario",
 [("Decir que no con claridad, aunque incomode", "Asertiva"),
  ("Buscar cómo ayudar sin dejar de lado lo tuyo", "Complaciente"),
  ("Tomarte un tiempo antes de contestar", "Retraída")]),

("N", "", "Lo que te da más seguridad al entrar a un lugar nuevo es:", "scenario",
 [("Saber que podes manejarte solo", "Asertiva"),
  ("Que alguien te presente y te ubique", "Complaciente"),
  ("Poder observar un rato antes de involucrarte", "Retraída")]),

("N", "", "Si un proyecto tuyo no avanza, tu reacción es:", "scenario",
 [("Forzar la situación hasta destrabarla", "Asertiva"),
  ("Buscar quién te ayude a moverlo", "Complaciente"),
  ("Replegarte y repensarlo desde cero", "Retraída")]),

("N", "", "Lo que más valorás de alguien con quien trabajás es:", "scenario",
 [("Que banque la presión y no afloje", "Asertiva"),
  ("Que sea confiable y cumpla lo que promete", "Complaciente"),
  ("Que respete tu espacio y no te encime", "Retraída")]),

("N", "", "Cuando el ambiente se pone tenso, vos:", "scenario",
 [("Vas al punto y lo destrabás", "Asertiva"),
  ("Intentás bajar la temperatura", "Complaciente"),
  ("Te corrés hasta que pase", "Retraída")]),

("N", "", "Lo que más te costaría de un jefe nuevo sería:", "scenario",
 [("Que te limite el margen de acción", "Asertiva"),
  ("No saber qué espera exactamente de vos", "Complaciente"),
  ("Que te estén encima mientras trabajás", "Retraída")]),

("N", "", "Cuando tenés una idea que sabés que va a generar resistencia:", "scenario",
 [("La presentás igual y defendés", "Asertiva"),
  ("La trabajás antes con los que van a resistirla", "Complaciente"),
  ("Esperás a tenerla tan sólida que no puedan objetarla", "Retraída")]),

("N", "", "Lo que más necesitás después de un conflicto es:", "scenario",
 [("Que quede resuelto de una vez", "Asertiva"),
  ("Saber que la relación sigue en pie", "Complaciente"),
  ("Estar un rato solo", "Retraída")]),

("N", "", "En una negociación, tu punto fuerte es:", "scenario",
 [("Sostener tu posición sin ceder de entrada", "Asertiva"),
  ("Encontrar el acuerdo que a todos les sirva", "Complaciente"),
  ("Haber estudiado el tema más que el otro", "Retraída")]),

("N", "", "Cuando alguien invade tu tiempo personal, lo que hacés es:", "scenario",
 [("Se lo decís ahí mismo", "Asertiva"),
  ("Dejarlo pasar por esta vez", "Complaciente"),
  ("Volverte menos disponible sin decir nada", "Retraída")]),

("N", "", "Lo que más te motiva de un logro es:", "scenario",
 [("Haber llegado antes o más lejos", "Asertiva"),
  ("Que sirva a los que dependían de vos", "Complaciente"),
  ("La satisfacción privada de haberlo hecho bien", "Retraída")]),

("N", "", "Si tenés que trabajar con alguien que no te cae bien:", "scenario",
 [("Se lo hacés notar de alguna forma", "Asertiva"),
  ("Te esforzás para que la relación funcione igual", "Complaciente"),
  ("Reducís el contacto al mínimo indispensable", "Retraída")]),

("N", "", "Lo que más te desgasta de la vida en grupo es:", "scenario",
 [("La lentitud para decidir", "Asertiva"),
  ("Tener que sostener el clima todo el tiempo", "Complaciente"),
  ("La falta de espacio propio", "Retraída")]),

("N", "", "Cuando te toca liderar sin haberlo pedido:", "scenario",
 [("Lo tomás naturalmente", "Asertiva"),
  ("Lo asumís por responsabilidad, aunque preferirías no", "Complaciente"),
  ("Buscás delegarlo o hacerlo lo más acotado posible", "Retraída")]),

("N", "", "Lo primero que hacés al llegar a un lugar donde no conocés a nadie es:", "scenario",
 [("Acercarte a alguien y arrancar conversación", "Asertiva"),
  ("Buscar a quien te pueda integrar al grupo", "Complaciente"),
  ("Ubicarte en un lugar tranquilo y mirar", "Retraída")]),

("N", "", "Si te enterás de que hablaron mal de vos, tu reacción es:", "scenario",
 [("Ir directo a encararlo", "Asertiva"),
  ("Preocuparte por reparar la relación", "Complaciente"),
  ("Alejarte de esa persona sin dar explicaciones", "Retraída")]),

("N", "", "Lo que más te cuesta de trabajar bajo reglas ajenas es:", "scenario",
 [("Que te frenen cuando ves el camino claro", "Asertiva"),
  ("Nada, te da tranquilidad saber qué se espera", "Complaciente"),
  ("Tener que rendir cuentas todo el tiempo", "Retraída")]),

("N", "", "Cuando algo te sale muy bien, lo que hacés con eso es:", "scenario",
 [("Capitalizarlo e ir por más", "Asertiva"),
  ("Compartirlo con quienes te acompañaron", "Complaciente"),
  ("Disfrutarlo puertas adentro", "Retraída")]),

("N", "", "Lo que más te ordena en un día caótico es:", "scenario",
 [("Tomar el control y priorizar vos", "Asertiva"),
  ("Saber que hay un plan y tu lugar en el", "Complaciente"),
  ("Conseguir un rato sin interrupciones", "Retraída")]),

("N", "", "Si tenés que dar una devolución negativa, lo más probable es que:", "scenario",
 [("La digas de frente y sin rodeos", "Asertiva"),
  ("La suavices para no lastimar", "Complaciente"),
  ("La postergues o la escribas en vez de decirla", "Retraída")]),

("N", "", "Lo que menos soportarías en una relación de trabajo es:", "scenario",
 [("Que te pasen por encima", "Asertiva"),
  ("Que se rompa la confianza", "Complaciente"),
  ("Que no respeten tu autonomía", "Retraída")]),

("N", "", "Cuando el grupo va en una dirección que no compartís:", "scenario",
 [("Lo planteás y tratás de cambiar el rumbo", "Asertiva"),
  ("Acompañás igual para no romper la unidad", "Complaciente"),
  ("Te desentendés y hacés lo tuyo aparte", "Retraída")]),

# --- Likert ---
("N", "", "Cuando quiero algo, voy directo a buscarlo aunque incomode a alguien.", "likert", "Asertiva"),
("N", "", "Me resulta natural tomar el mando cuando nadie lo está haciendo.", "likert", "Asertiva"),
("N", "", "Prefiero un conflicto abierto antes que una tensión que no se habla.", "likert", "Asertiva"),
("N", "", "Me cuesta decir que no cuando alguien me necesita.", "likert", "Complaciente"),
("N", "", "Suelo adaptar lo que quiero a lo que el grupo espera de mí.", "likert", "Complaciente"),
("N", "", "Me tranquiliza saber exactamente que se espera de mí.", "likert", "Complaciente"),
("N", "", "Necesito tiempo a solas para recuperar energía después de estar con gente.", "likert", "Retraída"),
("N", "", "Prefiero resolver mis problemas por mi cuenta antes que pedir ayuda.", "likert", "Retraída"),
("N", "", "Cuando la situación se tensa, mi primer impulso es alejarme.", "likert", "Retraída"),
]
