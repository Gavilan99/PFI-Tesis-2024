# -*- coding: utf-8 -*-
# Conjunto Armónico — Positiva / Competente / Reactiva
SYSTEM = "Conjunto Armónico"
GROUPS = ["Positiva", "Competente", "Reactiva"]
# Member types per group. Used by build.py to default and validate `type_coverage`.
GROUP_TYPES = {"Positiva": [2, 7, 9], "Competente": [1, 3, 5], "Reactiva": [4, 6, 8]}

ITEMS = [
("R", "Anexo C #1 — de reacción a que hacés con la frustración del obstáculo",
 "Cuando algo se interpone en un objetivo tuyo, lo que hacés con la frustración es:", "scenario",
 [("Correrla de foco y quedarte con lo que sí funciona", "Positiva"),
  ("Dejarla de lado y concentrarte en resolver", "Competente"),
  ("Expresarla, porque guardarla no te sirve", "Reactiva")]),

("R", "Anexo C #2 — la opción reactiva original ('manifiesto opiniones') no representaba al grupo",
 "Ante un problema que te desarma los planes, tu primera respuesta es:", "scenario",
 [("Confiar en que se va a acomodar", "Positiva"),
  ("Ponerte a resolverlo metódicamente", "Competente"),
  ("Reaccionar con intensidad antes de poder resolver", "Reactiva")]),

("R", "Anexo C #3 — de conducta a manejo del desvío",
 "Cuando las cosas no salen como esperabas, lo primero que hacés es:", "scenario",
 [("Buscarle el lado bueno a la nueva situación", "Positiva"),
  ("Identificar qué fallo y corregirlo", "Competente"),
  ("Registrar el fastidio y hacerlo saber", "Reactiva")]),

("R", "Anexo C #4 — apunta a qué se busca al resolver, no al método",
 "Cuando intervenís en un conflicto, lo que buscás conseguir es:", "scenario",
 [("Que vuelva la armonía y se disuelva la tensión", "Positiva"),
  ("Que quede resuelto de manera práctica y estable", "Competente"),
  ("Que se diga lo que realmente está pasando", "Reactiva")]),

("R", "Anexo C #5 — la opción reactiva original era confusa",
 "En una etapa difícil, lo que te sostiene es:", "scenario",
 [("Mantener la expectativa de que va a mejorar", "Positiva"),
  ("Tener claro el objetivo y el camino para llegar", "Competente"),
  ("La intensidad de lo que está en juego para vos", "Reactiva")]),

("R", "Anexo C #6 — de reacción a manejo del malestar que genera el otro",
 "Cuando alguien te resulta difícil de tratar, lo que hacés con eso es:", "scenario",
 [("Enfocarte en sus cosas buenas y seguir", "Positiva"),
  ("Manejarlo con distancia para que no afecte el resultado", "Competente"),
  ("Decirle lo que te molesta", "Reactiva")]),

("R", "Anexo C #7 — la opción reactiva original era contradictoria",
 "Frente a una tarea que no te interesa nada, lo que pasa es:", "scenario",
 [("Le encontrás algo disfrutable para hacerla llevadera", "Positiva"),
  ("La despachás rápido y eficientemente", "Competente"),
  ("Te cuesta arrancar y se te nota el fastidio", "Reactiva")]),

("R", "Anexo C #8 — de sentimiento a respuesta ante la falta de reconocimiento",
 "Cuando tu esfuerzo pasa desapercibido, lo que hacés es:", "scenario",
 [("Recordarte que el trabajo vale por sí mismo", "Positiva"),
  ("Seguir adelante; el reconocimiento no era el objetivo", "Competente"),
  ("Hacer notar que eso te cayó mal", "Reactiva")]),

("R", "Anexo C #9 — foco en el destino de la crítica inesperada",
 "Ante una crítica que no viste venir, lo que hacés con ella es:", "scenario",
 [("No dejar que te arruine el ánimo", "Positiva"),
  ("Evaluar si es válida y corregir si corresponde", "Competente"),
  ("Responder en el momento, con la emoción incluida", "Reactiva")]),

("R", "Anexo C #10 — la opción positiva original ('no pienso en la fecha') sonaba a negación",
 "Con un plazo encima y poco tiempo, lo que hacés es:", "scenario",
 [("Mantener la calma y confiar en que llegás", "Positiva"),
  ("Planificar y ejecutar para cumplir", "Competente"),
  ("Sentir la presión y hacerla visible", "Reactiva")]),

("R", "Anexo C #11 — de 'primer pensamiento' a que hacés con la interrupción",
 "Cuando algo interrumpe lo que tenías planeado, lo primero que hacés es:", "scenario",
 [("Ver qué se puede rescatar de la nueva situación", "Positiva"),
  ("Reorganizar para retomar el curso", "Competente"),
  ("Registrar lo injusto de la interrupción", "Reactiva")]),

("N", "", "Cuando alguien te decepciona, lo que hacés con esa decepcion es:", "scenario",
 [("Minimizarla y darle otra oportunidad", "Positiva"),
  ("Recalibrar qué podés esperar de esa persona", "Competente"),
  ("Planteárselo, aunque genere tensión", "Reactiva")]),

("N", "", "Lo que más te cuesta de una mala noticia es:", "scenario",
 [("Perder el clima bueno que había", "Positiva"),
  ("Tener que rearmar todo el plan", "Competente"),
  ("Que te pidan que la tomes con calma", "Reactiva")]),

("N", "", "Cuando estás de mal humor, lo más probable es que:", "scenario",
 [("Trates de levantarlo haciendo algo lindo", "Positiva"),
  ("Sigas funcionando igual, sin que se note", "Competente"),
  ("Se note enseguida", "Reactiva")]),

("N", "", "Frente a un error propio, tu reacción honesta es:", "scenario",
 [("Relativizarlo rápido", "Positiva"),
  ("Analizarlo para que no se repita", "Competente"),
  ("Fastidiarte bastante con vos mismo", "Reactiva")]),

("N", "", "Lo que más valorás de alguien en un momento difícil es:", "scenario",
 [("Que te levante el ánimo", "Positiva"),
  ("Que te ayude a resolverlo", "Competente"),
  ("Que banque tu estado sin pedirte que lo cambies", "Reactiva")]),

("N", "", "Cuando algo te duele, lo que hacés con ese dolor es:", "scenario",
 [("Buscar distraerte hasta que pase", "Positiva"),
  ("Entenderlo para poder administrarlo", "Competente"),
  ("Atravesarlo de lleno, sin esquivarlo", "Reactiva")]),

("N", "", "Lo que te resulta más insoportable de una situación estancada es:", "scenario",
 [("El clima pesado que se genera", "Positiva"),
  ("La ineficiencia de no avanzar", "Competente"),
  ("Que nadie diga lo que todos ven", "Reactiva")]),

("N", "", "Si un plan falla por culpa de otro, lo más probable es que:", "scenario",
 [("Lo dejes pasar para no arruinar el vínculo", "Positiva"),
  ("Ajustes el proceso para que no vuelva a pasar", "Competente"),
  ("Se lo digas en el momento", "Reactiva")]),

("N", "", "Lo que más te ayuda a superar un mal momento es:", "scenario",
 [("Recordar que ya pasaste por cosas peores", "Positiva"),
  ("Tener una tarea clara donde poner la cabeza", "Competente"),
  ("Poder descargarlo con alguien de confianza", "Reactiva")]),

("N", "", "Cuando alguien te pide que bajes un cambio, lo que sentís es:", "scenario",
 [("Que tiene razon, mejor no cargar el clima", "Positiva"),
  ("Que es razonable, la emoción no ayuda a resolver", "Competente"),
  ("Que te están pidiendo que seas falso", "Reactiva")]),

("N", "", "Lo primero que evaluás al encarar un problema es:", "scenario",
 [("Cuánto va a costar en términos de clima", "Positiva"),
  ("Cuál es la vía más eficiente para resolverlo", "Competente"),
  ("Qué tan grave es realmente", "Reactiva")]),

("N", "", "Cuando algo importante se frustra, lo que necesitás primero es:", "scenario",
 [("Que alguien te diga que va a estar bien", "Positiva"),
  ("Entender qué se puede hacer ahora", "Competente"),
  ("Que se reconozca que fue un golpe", "Reactiva")]),

("N", "", "Lo que más te molesta de una conversación superficial es:", "scenario",
 [("Nada, está bien que no todo sea profundo", "Positiva"),
  ("Que se pierda tiempo sin llegar a nada", "Competente"),
  ("Que se esquive lo que realmente importa", "Reactiva")]),

("N", "", "Ante una injusticia que te toca de cerca, tu respuesta es:", "scenario",
 [("Buscar el modo de que igual salga algo bueno", "Positiva"),
  ("Ver qué se puede hacer concretamente", "Competente"),
  ("Reaccionar con toda la intensidad que te genera", "Reactiva")]),

("N", "", "Lo que más te cuesta sostener en el tiempo es:", "scenario",
 [("La atención sobre lo que no funciona", "Positiva"),
  ("La paciencia cuando el sistema no acompaña", "Competente"),
  ("La calma cuando algo te importa mucho", "Reactiva")]),

("N", "", "Si tenés que elegir cómo te acompañen en una crisis, preferís:", "scenario",
 [("Alguien que le ponga liviandad", "Positiva"),
  ("Alguien que ordene y proponga", "Competente"),
  ("Alguien que se enoje con vos", "Reactiva")]),

("N", "", "Lo que hacés cuando algo te satura es:", "scenario",
 [("Cambiar de tema o de actividad", "Positiva"),
  ("Sistematizar hasta volverlo manejable", "Competente"),
  ("Estallar un poco y después acomodarte", "Reactiva")]),

("N", "", "Frente a una promesa incumplida, lo que aparece es:", "scenario",
 [("La tendencia a justificar al otro", "Positiva"),
  ("La necesidad de rearmar sin contar con eso", "Competente"),
  ("El enojo, y las ganas de decirlo", "Reactiva")]),

("N", "", "Lo que más te define frente a una dificultad grande es:", "scenario",
 [("Que no perdes el optimismo", "Positiva"),
  ("Que encontrás la forma de resolverlo", "Competente"),
  ("Que la vivis con toda la intensidad", "Reactiva")]),

("N", "", "Cuando el clima de un grupo se enrarece, lo que hacés es:", "scenario",
 [("Intentar aligerarlo", "Positiva"),
  ("Enfocarte en la tarea igual", "Competente"),
  ("Nombrar lo que está pasando", "Reactiva")]),

("N", "", "Lo que menos te gusta de vos en los momentos malos es:", "scenario",
 [("Que a veces evitás mirar el problema de frente", "Positiva"),
  ("Que te volvés frío con la gente", "Competente"),
  ("Que se te desborda la reacción", "Reactiva")]),

("N", "", "Al recibir una devolución dura pero justa, lo que hacés primero es:", "scenario",
 [("Rescatar lo positivo que también te dijeron", "Positiva"),
  ("Separar el dato útil del tono", "Competente"),
  ("Sentirlo fuerte antes de poder usarlo", "Reactiva")]),

("N", "", "Lo que buscás cuando algo te sale mal es:", "scenario",
 [("Recuperar el buen ánimo cuanto antes", "Positiva"),
  ("Recuperar el control de la situación", "Competente"),
  ("Que se registre que la situación fue mala", "Reactiva")]),

("N", "", "Si algo te preocupa mucho, lo más probable es que los demás:", "scenario",
 [("Ni se enteren, porque seguís con buena cara", "Positiva"),
  ("Vean que estás más concentrado que de costumbre", "Competente"),
  ("Se den cuenta enseguida", "Reactiva")]),

("N", "", "Lo que más te ordena en un momento de caos emocional es:", "scenario",
 [("Recordar que va a pasar", "Positiva"),
  ("Volver a lo concreto y ejecutable", "Competente"),
  ("Ponerle nombre a lo que sentís", "Reactiva")]),

("N", "", "Cuando alguien minimiza algo que te afectó, sentís:", "scenario",
 [("Alivio, quizás era menos grave de lo que pensabas", "Positiva"),
  ("Indiferencia, lo importante es que se resuelva", "Competente"),
  ("Que no te están tomando en serio", "Reactiva")]),

("N", "", "Lo que más te agota de una relación complicada es:", "scenario",
 [("La cantidad de conflicto acumulado", "Positiva"),
  ("La ineficacia de no poder resolverlo", "Competente"),
  ("Tener que medir todo lo que decís", "Reactiva")]),

("N", "", "Frente a un fracaso, lo primero que te decís es:", "scenario",
 [("Algo bueno va a salir de esto", "Positiva"),
  ("Veamos qué se hace ahora", "Competente"),
  ("Esto duele y no voy a fingir que no", "Reactiva")]),

("N", "", "Lo que más necesitás de un equipo cuando las cosas van mal es:", "scenario",
 [("Que no se caiga el ánimo", "Positiva"),
  ("Que cada uno haga bien su parte", "Competente"),
  ("Que se hable con sinceridad de lo que pasa", "Reactiva")]),

("N", "", "Cuando algo te sale mal por tu propia culpa, lo que hacés con eso es:", "scenario",
 [("Perdonártelo rápido y seguir", "Positiva"),
  ("Convertirlo en un aprendizaje concreto", "Competente"),
  ("Masticarlo un buen rato antes de soltarlo", "Reactiva")]),

# --- Likert ---
("N", "", "Cuando algo sale mal, tiendo a enfocarme rápido en lo que sí está funcionando.", "likert", "Positiva"),
("N", "", "Me incomoda quedarme mucho tiempo en una conversación negativa.", "likert", "Positiva"),
("N", "", "Prefiero no cargar a los demás con mis problemas.", "likert", "Positiva"),
("N", "", "Frente a una dificultad, lo primero que busco es la solución más eficiente.", "likert", "Competente"),
("N", "", "Puedo dejar de lado lo que siento si eso me permite resolver mejor.", "likert", "Competente"),
("N", "", "Me resulta natural apoyarme en reglas y procedimientos claros.", "likert", "Competente"),
("N", "", "Cuando algo me afecta, se me nota aunque no quiera.", "likert", "Reactiva"),
("N", "", "Necesito que los demás respondan con la misma intensidad que yo pongo.", "likert", "Reactiva"),
("N", "", "Prefiero una discusión sincera antes que una calma fingida.", "likert", "Reactiva"),
]
