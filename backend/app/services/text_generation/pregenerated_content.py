# DRAFT: pending human review before this is merged (see the module docstring below).
"""Pregenerated content (Feature 19) for the result screen's four personalized sections —
strengths, tensions, growth, stress — one entry per eneatype and account type.

A human has not reviewed this content yet: it is a draft, written to the same rules as
SYSTEM_PROMPT, meant to be read and corrected before this file reaches `TEXT_GENERATOR=pregenerated`
or `TEXT_GENERATOR=bedrock` in production. Nothing in the code gates on that — the DRAFT marker above
is for the person reviewing the diff, not a runtime check.

Used by `app.services.personalized_descriptions` two ways: as a complete provider with
TEXT_GENERATOR=pregenerated (the endpoint never calls a model), and as a fallback when a Bedrock
generation fails or doesn't pass the format validation (TEXT_GENERATOR=bedrock). It never goes
through the FORTALEZAS/TENSIONES/CRECIMIENTO/ESTRES marker format or its parser: it's already
structured as lists and paragraphs, the same shape that parser produces.

Same register and the same content rules as SYSTEM_PROMPT (Spanish rioplatense with voseo, no
diagnosis or clinical language, based only on each eneatype's generic description in
`app.services.result_descriptions` / `eneatype-content.ts`, without contradicting it or adding traits
of other eneatypes), but adapted to the account type instead of to a person's profile: "individual"
is personal self-knowledge, "salud" assumes a health professional's accompaniment, "rrhh" frames it
for the workplace. Unlike what a model generates, this is fixed per eneatype and account type — it
never uses age or professional context, because there is no profile to take them from.

The 27 entries (9 eneatypes x 3 account types) must pass the same length and count validation
`app.services.personalized_descriptions` applies to a parsed Bedrock answer
(`tests/test_pregenerated_content.py`).
"""

from app.db.models.enums import AccountType

PregeneratedEntry = dict[str, list[str] | str]

PREGENERATED_CONTENT: dict[tuple[int, AccountType], PregeneratedEntry] = {
    (1, AccountType.INDIVIDUAL): {
        "strengths": [
            "Tenés un sentido de lo justo muy claro y lo sostenés aunque cueste.",
            "Cuidás los detalles y la calidad de lo que hacés.",
            "Sos coherente entre lo que decís y lo que hacés.",
            "Te hacés cargo de la responsabilidad que te toca.",
        ],
        "tensions": [
            "Podés ser muy duro con vos mismo cuando algo no sale perfecto.",
            "Te cuesta dar algo por terminado si no quedó impecable.",
            "A veces te guardás el enojo cuando algo te parece injusto.",
            "Podés pensar que hay un único modo correcto de hacer las cosas.",
        ],
        "growth": (
            "Cuando estás en tu mejor momento, te permitís disfrutar y equivocarte sin que eso te "
            "pese tanto. Tu exigencia se vuelve más amable, con vos y con los demás, y eso te deja "
            "más liviano en el día a día."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, tendés a volverte más rígido y crítico, como si todo "
            "dependiera de que vos lo corrijas. Ahí es fácil que se te acumule el cansancio de "
            "querer controlarlo todo."
        ),
    },
    (1, AccountType.SALUD): {
        "strengths": [
            "Llegás a este espacio con un sentido de lo justo muy claro, que podés poner en palabras.",
            "Cuidás los detalles de lo que te pasa y eso ayuda a que el acompañamiento sea preciso.",
            "Sos coherente entre lo que contás y lo que hacés, algo valioso para quien te acompaña.",
            "Te hacés cargo de lo que te toca, incluso cuando no es cómodo.",
        ],
        "tensions": [
            "Podés ser muy exigente con vos mismo, también en este proceso.",
            "Te cuesta dar por cerrado un tema si sentís que no quedó resuelto del todo.",
            "A veces te guardás el enojo en lugar de nombrarlo en el espacio de acompañamiento.",
            "Podés pensar que hay una sola forma correcta de encarar lo que te pasa.",
        ],
        "growth": (
            "En este acompañamiento, tu profesional de salud puede ayudarte a soltar un poco esa "
            "exigencia y a animarte a probar sin que todo tenga que salir perfecto. Eso te deja más "
            "espacio para disfrutar del proceso."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés volverte más rígido y crítico con vos mismo, y "
            "sentir que todo depende de que lo corrijas solo. Contárselo a quien te acompaña puede "
            "aliviar ese peso."
        ),
    },
    (1, AccountType.RRHH): {
        "strengths": [
            "Tenés un sentido de lo justo muy claro, que se nota en cómo trabajás.",
            "Cuidás los detalles y la calidad de lo que entregás al equipo.",
            "Sos coherente entre lo que decís y lo que hacés en tu rol.",
            "Te hacés cargo de la responsabilidad que te toca sin esquivarla.",
        ],
        "tensions": [
            "Podés ser muy exigente con tus compañeros, aunque no sea tu intención.",
            "Te cuesta delegar o cerrar una tarea si no quedó impecable.",
            "A veces te guardás el enojo cuando algo en el equipo te parece injusto.",
            "Podés insistir en que hay una sola forma correcta de hacer las cosas.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, te permitís soltar un poco el control y dejar "
            "que otros aporten su propia forma de hacer las cosas. Tu exigencia se vuelve más "
            "amable y contagia calidad sin tanta tensión."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés volverte más rígido y crítico con tus compañeros, "
            "sintiendo que todo depende de que vos lo corrijas. Ahí conviene que puedas nombrar esa "
            "carga en vez de cargarla solo."
        ),
    },
    (2, AccountType.INDIVIDUAL): {
        "strengths": [
            "Percibís rápido cómo está la otra persona y eso te hace cercano.",
            "Te ofrecés a ayudar sin que te lo pidan.",
            "Creás vínculos cálidos con bastante facilidad.",
            "Sos generoso con tu tiempo y tu energía.",
        ],
        "tensions": [
            "Podés dejar tus propias necesidades para después.",
            "Te cuesta pedir ayuda o decir que no.",
            "A veces esperás algo a cambio de lo que das, aunque no lo digas.",
            "Te dolés cuando sentís que tu esfuerzo no se nota.",
        ],
        "growth": (
            "En tu mejor versión, te cuidás con la misma atención que les dedicás a los demás. "
            "Ayudás porque querés, no para ganarte un lugar, y eso te deja más liviano y más "
            "conectado con lo que realmente necesitás."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés insistir con tu ayuda aunque no te la pidan y "
            "sentir que nadie valora lo que hacés. Ahí es un buen momento para preguntarte qué "
            "necesitás vos, además de dar."
        ),
    },
    (2, AccountType.SALUD): {
        "strengths": [
            "Percibís con facilidad cómo está el otro, algo que te hace sensible al acompañamiento.",
            "Te ofrecés a ayudar sin que te lo pidan, incluso en momentos difíciles.",
            "Generás vínculos cálidos con quienes te rodean.",
            "Sos generoso con tu tiempo, también en este proceso.",
        ],
        "tensions": [
            "Podés dejar de lado lo que a vos te pasa para ocuparte de los demás.",
            "Te cuesta pedir ayuda, incluso dentro de este acompañamiento.",
            "A veces esperás reconocimiento por lo que das sin decirlo abiertamente.",
            "Te dolés cuando sentís que tu esfuerzo no es visto.",
        ],
        "growth": (
            "En este acompañamiento, podés aprender a cuidarte con la misma atención que le das a "
            "los demás. Tu profesional de salud puede ayudarte a poner en palabras lo que "
            "necesitás vos, no solo lo que necesitan otros."
        ),
        "stress": (
            "Bajo mucha presión, podés insistir en ayudar aunque no te lo pidan y sentir que tu "
            "esfuerzo pasa desapercibido. Hablar de eso en el espacio de acompañamiento ayuda a "
            "aliviar esa sensación."
        ),
    },
    (2, AccountType.RRHH): {
        "strengths": [
            "Percibís rápido cómo está tu equipo y eso suma al clima de trabajo.",
            "Te ofrecés a ayudar a tus compañeros sin que te lo pidan.",
            "Generás vínculos cálidos dentro del equipo.",
            "Sos generoso con tu tiempo cuando alguien lo necesita.",
        ],
        "tensions": [
            "Podés dejar tus propias tareas para después por ocuparte de las de otros.",
            "Te cuesta decir que no cuando te piden una mano de más.",
            "A veces esperás que se reconozca lo que hacés por el equipo.",
            "Te dolés cuando tu esfuerzo en el trabajo no se nota.",
        ],
        "growth": (
            "En tu mejor versión en el equipo, cuidás tu propia carga de trabajo con la misma "
            "atención que le das a la de los demás. Ayudás porque querés, no para ganarte un "
            "lugar, y eso fortalece tus vínculos laborales."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés insistir en ayudar a todos aunque eso te desborde, "
            "y sentir que nadie valora lo que hacés. Ahí conviene que puedas poner un límite y "
            "pedir ayuda también para vos."
        ),
    },
    (3, AccountType.INDIVIDUAL): {
        "strengths": [
            "Te fijás objetivos y los cumplís con energía.",
            "Te adaptás rápido a lo que pide cada situación.",
            "Sabés presentar bien tus ideas.",
            "Priorizás lo que da resultados concretos.",
        ],
        "tensions": [
            "Podés medir tu valor solo por lo que lográs.",
            "Dejás de lado lo que sentís para no frenar.",
            "Tendés a mostrar la versión de vos que más conviene.",
            "Te cuesta bajar el ritmo y simplemente parar.",
        ],
        "growth": (
            "En tu mejor versión, te mostrás como sos y no solo por lo que rendís. Descubrís que "
            "tu valor no depende de cada logro, y eso te permite disfrutar del camino tanto como "
            "del resultado."
        ),
        "stress": (
            "Bajo estrés, podés exigirte cada vez más para no sentir que fallaste, aunque eso te "
            "aleje de lo que realmente sentís. Ahí es cuando más te conviene frenar un momento y "
            "preguntarte cómo estás."
        ),
    },
    (3, AccountType.SALUD): {
        "strengths": [
            "Tenés energía y foco para encarar lo que te propongas, también este proceso.",
            "Te adaptás rápido a lo que haga falta en cada momento.",
            "Podés poner en palabras tus ideas con claridad.",
            "Priorizás lo que te da resultados concretos.",
        ],
        "tensions": [
            "Podés medir tu valor por lo que lográs, incluso en tu propio bienestar.",
            "Dejás de lado lo que sentís para seguir avanzando.",
            "Tendés a mostrar la versión de vos que te parece más presentable, también acá.",
            "Te cuesta bajar el ritmo y darte un espacio de pausa.",
        ],
        "growth": (
            "En este acompañamiento, podés animarte a mostrarte como sos, más allá de lo que "
            "lográs. Tu profesional de salud puede ayudarte a conectar con lo que sentís, no solo "
            "con lo que hacés."
        ),
        "stress": (
            "Bajo mucha presión, podés exigirte cada vez más para no sentir que fallaste, dejando "
            "de lado lo que te pasa por dentro. Nombrar eso en el acompañamiento ayuda a bajar esa "
            "exigencia."
        ),
    },
    (3, AccountType.RRHH): {
        "strengths": [
            "Te fijás objetivos claros y los llevás adelante con energía.",
            "Contagiás empuje a tu equipo.",
            "Te adaptás rápido a lo que pide cada proyecto.",
            "Sabés presentar bien tus ideas frente a otros.",
        ],
        "tensions": [
            "Podés medir tu valor solo por los resultados que mostrás en el trabajo.",
            "Dejás de lado lo que sentís para no frenar el ritmo del equipo.",
            "Tendés a mostrar la versión de vos que más conviene de cara a los demás.",
            "Te cuesta bajar el ritmo, aunque el equipo lo necesite.",
        ],
        "growth": (
            "En tu mejor versión como parte del equipo, te mostrás auténtico, con dudas y todo, y "
            "valorás los vínculos tanto como los resultados. Eso fortalece la confianza con tus "
            "compañeros."
        ),
        "stress": (
            "Bajo presión laboral, podés exigirte cada vez más para no sentir que fallaste frente "
            "al equipo. Ahí conviene que puedas compartir cómo estás en lugar de seguir empujando "
            "solo."
        ),
    },
    (4, AccountType.INDIVIDUAL): {
        "strengths": [
            "Ponés en palabras lo que otros no saben decir.",
            "Tenés una mirada original sobre las cosas.",
            "Te conocés bien por dentro.",
            "Encontrás sentido y belleza en lo cotidiano.",
        ],
        "tensions": [
            "Tu estado de ánimo puede cambiar bastante de un momento a otro.",
            "Podés sentir que te falta algo que otros sí tienen.",
            "Tendés a encerrarte en lo que sentís.",
            "Te cuesta valorar lo que ya tenés.",
        ],
        "growth": (
            "En tu mejor versión, dejás de buscar lo que te falta y te sentís a gusto con quien ya "
            "sos. Tu creatividad se vuelca hacia afuera y empieza a transformarse en algo que "
            "podés compartir."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés sentir que nadie te entiende y replegarte en tu "
            "mundo interior. Ahí es cuando más te ayuda buscar a alguien de confianza para "
            "compartir lo que te pasa."
        ),
    },
    (4, AccountType.SALUD): {
        "strengths": [
            "Podés poner en palabras lo que te pasa con mucha profundidad.",
            "Tenés una mirada propia sobre lo que vivís.",
            "Te conocés bien por dentro, algo valioso para este proceso.",
            "Encontrás sentido incluso en los momentos difíciles.",
        ],
        "tensions": [
            "Tu estado de ánimo puede cambiar bastante, también durante este acompañamiento.",
            "Podés sentir que te falta algo que a otros les resulta más fácil.",
            "Tendés a encerrarte en lo que sentís en lugar de compartirlo.",
            "Te cuesta valorar los avances que ya hiciste.",
        ],
        "growth": (
            "En este acompañamiento, podés ir sintiéndote más a gusto con quien sos, sin "
            "compararte tanto con los demás. Tu profesional de salud puede ayudarte a transformar "
            "lo que sentís en algo que podés compartir."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés sentir que nadie te entiende del todo y "
            "encerrarte en tu mundo interior. Contárselo a quien te acompaña, aunque sea difícil, "
            "ayuda a que ese peso baje."
        ),
    },
    (4, AccountType.RRHH): {
        "strengths": [
            "Aportás una mirada original que enriquece al equipo.",
            "Podés poner en palabras cosas que otros no saben expresar.",
            "Te conocés bien y eso te da claridad sobre lo que te hace bien en el trabajo.",
            "Le ponés sentido propio a lo que hacés.",
        ],
        "tensions": [
            "Tu ánimo puede variar bastante de un día a otro en el trabajo.",
            "Podés sentir que no encajás del todo con la dinámica del equipo.",
            "Tendés a encerrarte en lo que sentís en lugar de compartirlo con tus compañeros.",
            "Te cuesta valorar los logros que ya conseguiste.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, te sentís más a gusto con tu propio estilo y "
            "lo ponés al servicio de lo que hacen todos. Eso te permite aportar tu mirada sin "
            "sentir que tenés que encajar en un molde."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés sentir que nadie entiende tu forma de ver las cosas "
            "y aislarte un poco del equipo. Compartir lo que te pasa con alguien de confianza "
            "ayuda a que no se acumule."
        ),
    },
    (5, AccountType.INDIVIDUAL): {
        "strengths": [
            "Investigás a fondo antes de opinar.",
            "Mantenés la cabeza fría cuando hay tensión alrededor.",
            "Te arreglás bien por tu cuenta.",
            "Aportás ideas que otros no vieron.",
        ],
        "tensions": [
            "Podés tomar distancia de lo que sentís.",
            "Te cuesta pedir o mostrar lo que necesitás.",
            "Tendés a analizar en lugar de actuar.",
            "Compartís poco de tu vida personal.",
        ],
        "growth": (
            "En tu mejor versión, te animás a actuar con lo que ya sabés, sin esperar tener toda "
            "la información. También te permitís compartir más de vos con las personas en las que "
            "confiás."
        ),
        "stress": (
            "Cuando te sentís exigido, podés replegarte, guardar tu energía y quedarte pensando en "
            "lugar de involucrarte. Ahí ayuda recordar que no tenés que resolverlo todo en soledad."
        ),
    },
    (5, AccountType.SALUD): {
        "strengths": [
            "Observás con atención lo que te pasa antes de sacar conclusiones.",
            "Mantenés la calma incluso cuando el tema es difícil.",
            "Te manejás bien de forma autónoma en tu día a día.",
            "Pensás con claridad e independencia.",
        ],
        "tensions": [
            "Podés tomar distancia de lo que sentís, también en este espacio.",
            "Te cuesta pedir o mostrar lo que necesitás, incluso a quien te acompaña.",
            "Tendés a analizar la situación en lugar de hablar de cómo te afecta.",
            "Compartís poco de tu vida personal, aun en el acompañamiento.",
        ],
        "growth": (
            "En este acompañamiento, podés ir animándote a compartir más de lo que sentís, no "
            "solo de lo que pensás. Tu profesional de salud puede ayudarte a traducir en palabras "
            "lo que normalmente te guardás."
        ),
        "stress": (
            "Cuando te sentís exigido, podés replegarte y quedarte pensando en lugar de pedir "
            "ayuda. Contarle a quien te acompaña lo que te pasa, aunque sea en pocas palabras, ya "
            "es un paso importante."
        ),
    },
    (5, AccountType.RRHH): {
        "strengths": [
            "Investigás a fondo antes de proponer algo al equipo.",
            "Mantenés la cabeza fría cuando hay tensión en el trabajo.",
            "Te manejás bien de forma autónoma en tus tareas.",
            "Aportás ideas que otros no vieron.",
        ],
        "tensions": [
            "Podés tomar distancia de lo que sentís respecto al trabajo.",
            "Te cuesta pedir ayuda o mostrar lo que necesitás frente al equipo.",
            "Tendés a analizar en lugar de actuar cuando hay que decidir rápido.",
            "Compartís poco de vos con tus compañeros.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, te animás a actuar con lo que ya sabés y a "
            "compartir un poco más de vos con quienes trabajás. Eso fortalece la confianza sin que "
            "tengas que cambiar tu forma de ser."
        ),
        "stress": (
            "Cuando te sentís exigido en el trabajo, podés aislarte y guardar tu energía en lugar "
            "de involucrarte con el equipo. Ahí ayuda avisar que necesitás espacio, en lugar de "
            "desaparecer sin decir nada."
        ),
    },
    (6, AccountType.INDIVIDUAL): {
        "strengths": [
            "Cumplís con lo que te comprometés.",
            "Anticipás los problemas antes de que pasen.",
            "Defendés a los tuyos cuando hace falta.",
            "Sos alguien con quien se puede contar.",
        ],
        "tensions": [
            "Podés preocuparte de más por lo que todavía no pasó.",
            "Dudás de tus propias decisiones.",
            "Tendés a desconfiar de lo que no conocés.",
            "Buscás la aprobación de otros antes de avanzar.",
        ],
        "growth": (
            "En tu mejor versión, confiás en tu propio criterio. La seguridad que buscabas afuera "
            "la vas encontrando en vos, y eso te permite avanzar sin necesitar tantas garantías "
            "previas."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés llenarte de dudas y dar muchas vueltas antes de "
            "decidir. Ahí ayuda recordar que no hace falta tener la certeza completa para dar el "
            "paso."
        ),
    },
    (6, AccountType.SALUD): {
        "strengths": [
            "Sos previsor y eso te ayuda a anticipar lo que puede pasar.",
            "Te comprometés con lo que decidís hacer en este proceso.",
            "Sos leal a las personas y a los espacios en los que confiás.",
            "Sos alguien en quien se puede confiar.",
        ],
        "tensions": [
            "Podés preocuparte de más por cómo va a seguir este proceso.",
            "Dudás de tus propias decisiones, incluso las que ya tomaste.",
            "Tendés a desconfiar de lo que todavía no conocés bien.",
            "Buscás la aprobación de quien te acompaña antes de animarte a algo nuevo.",
        ],
        "growth": (
            "En este acompañamiento, podés ir confiando más en tu propio criterio. Tu profesional "
            "de salud puede ayudarte a apoyarte en lo que ya sabés de vos, en lugar de necesitar "
            "certezas externas para cada paso."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés llenarte de dudas y darle vueltas a lo mismo "
            "antes de decidir. Compartir esas dudas en el espacio de acompañamiento ayuda a que "
            "pesen menos."
        ),
    },
    (6, AccountType.RRHH): {
        "strengths": [
            "Cumplís con lo que te comprometés frente al equipo.",
            "Anticipás los problemas antes de que afecten al trabajo.",
            "Defendés a tus compañeros cuando hace falta.",
            "Sos alguien con quien el equipo puede contar.",
        ],
        "tensions": [
            "Podés preocuparte de más por cómo vienen las cosas en el trabajo.",
            "Dudás de tus propias decisiones, aunque tengas la información necesaria.",
            "Tendés a desconfiar de los cambios o de lo que no conocés bien.",
            "Buscás la aprobación de otros antes de avanzar con una idea.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, confiás más en tu propio criterio y te animás "
            "a proponer sin esperar el visto bueno de todos. Eso te permite aportar con más "
            "seguridad."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés llenarte de dudas y postergar una decisión dándole "
            "muchas vueltas. Ahí ayuda compartir esas dudas con alguien del equipo en lugar de "
            "cargarlas solo."
        ),
    },
    (7, AccountType.INDIVIDUAL): {
        "strengths": [
            "Contagiás buen humor a quienes te rodean.",
            "Ves oportunidades donde otros ven problemas.",
            "Te interesan muchos temas distintos.",
            "Arrancás proyectos con mucha energía.",
        ],
        "tensions": [
            "Te cuesta terminar lo que empezás.",
            "Podés esquivar las conversaciones incómodas.",
            "A veces decidís sin medir del todo las consecuencias.",
            "Te aburrís rápido de la rutina.",
        ],
        "growth": (
            "En tu mejor versión, te quedás con lo que elegiste aunque deje de ser novedad. Ahí "
            "descubrís que profundizar en algo también puede darte la satisfacción que buscabas "
            "en lo nuevo."
        ),
        "stress": (
            "Cuando te sentís encerrado por tus compromisos, podés perder la paciencia cuando las "
            "cosas no salen como las imaginabas. Ahí conviene frenar un momento antes de sumar un "
            "plan más."
        ),
    },
    (7, AccountType.SALUD): {
        "strengths": [
            "Tenés una energía positiva que te ayuda a encarar este proceso.",
            "Te interesás por entender lo que te pasa desde distintos ángulos.",
            "Te adaptás rápido a los cambios que puedan surgir.",
            "Encontrás el lado más llevadero incluso en momentos difíciles.",
        ],
        "tensions": [
            "Te cuesta sostener un proceso cuando deja de sentirse novedoso.",
            "Podés esquivar las conversaciones que te resultan incómodas.",
            "A veces decidís sin medir del todo las consecuencias.",
            "Te aburrís rápido si sentís que es siempre lo mismo.",
        ],
        "growth": (
            "En este acompañamiento, te ayuda quedarte con el proceso aunque deje de sentirse "
            "nuevo. Tu profesional de salud puede acompañarte a encontrarle sentido a sostener "
            "algo en el tiempo."
        ),
        "stress": (
            "Cuando sentís que el proceso te limita, podés perder la paciencia y querer dejarlo o "
            "cambiarlo de golpe. Hablar de esa inquietud en el espacio de acompañamiento ayuda a "
            "no actuar solo por impulso."
        ),
    },
    (7, AccountType.RRHH): {
        "strengths": [
            "Contagiás buen humor y energía al equipo.",
            "Ves oportunidades donde otros ven solo problemas.",
            "Te interesan muchos temas y eso enriquece al grupo.",
            "Arrancás proyectos nuevos con mucho entusiasmo.",
        ],
        "tensions": [
            "Te cuesta terminar lo que empezás dentro de un proyecto.",
            "Podés esquivar las conversaciones incómodas con el equipo.",
            "A veces decidís rápido sin medir del todo las consecuencias para el trabajo.",
            "Te aburrís rápido de las tareas repetitivas.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, te quedás con un proyecto el tiempo que hace "
            "falta, aunque ya no sea novedoso. Eso te permite profundizar y sostener resultados, "
            "no solo arrancarlos."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés sentirte encerrado por tus compromisos y perder la "
            "paciencia con el ritmo del equipo. Ahí ayuda frenar antes de sumar una tarea más de "
            "las que ya tenés."
        ),
    },
    (8, AccountType.INDIVIDUAL): {
        "strengths": [
            "Tomás decisiones y te hacés cargo de ellas.",
            "Protegés a la gente que querés.",
            "Decís lo que pensás sin vueltas.",
            "Ponés en marcha lo que otros dudan en empezar.",
        ],
        "tensions": [
            "Podés imponerte sin darte cuenta.",
            "Te cuesta mostrarte frágil.",
            "Preferís no depender de nadie.",
            "Podés reaccionar con demasiada intensidad.",
        ],
        "growth": (
            "En tu mejor versión, usás tu fuerza para cuidar más que para controlar. Te permitís "
            "mostrar tu lado más sensible, y eso no te hace menos fuerte, sino más cercano."
        ),
        "stress": (
            "Cuando sentís que las cosas se te van de las manos, podés ponerte a la defensiva y "
            "endurecerte. Ahí ayuda recordar que pedir una mano no es lo mismo que perder el "
            "control."
        ),
    },
    (8, AccountType.SALUD): {
        "strengths": [
            "Tenés una energía y una firmeza que te ayudan a atravesar momentos difíciles.",
            "Decís lo que pensás con claridad, también en este proceso.",
            "Te hacés cargo de lo que te toca sin esquivarlo.",
            "Protegés lo que te importa.",
        ],
        "tensions": [
            "Te cuesta mostrarte frágil, incluso frente a quien te acompaña.",
            "Preferís manejar las cosas solo antes que depender de otros.",
            "Podés reaccionar con intensidad cuando algo te incomoda.",
            "Tenés poca paciencia con los procesos que sentís lentos.",
        ],
        "growth": (
            "En este acompañamiento, podés ir animándote a mostrar tu lado más sensible. Tu "
            "profesional de salud puede ayudarte a ver que compartir lo que te cuesta no te resta "
            "fuerza."
        ),
        "stress": (
            "Cuando sentís que las cosas se te van de las manos, podés ponerte a la defensiva y "
            "cerrarte. Nombrar eso en el espacio de acompañamiento, aunque sea difícil, ayuda a "
            "aflojar esa tensión."
        ),
    },
    (8, AccountType.RRHH): {
        "strengths": [
            "Tomás decisiones y te hacés cargo de ellas frente al equipo.",
            "Protegés a tus compañeros cuando hace falta.",
            "Decís lo que pensás sin vueltas en las reuniones.",
            "Impulsás lo que otros dudan en empezar.",
        ],
        "tensions": [
            "Podés imponerte sin darte cuenta frente al resto del equipo.",
            "Te cuesta mostrarte frágil en el trabajo.",
            "Preferís resolver las cosas solo antes que pedir ayuda.",
            "Tenés poca paciencia con la indecisión de otros.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, usás tu fuerza para impulsar a los demás en "
            "lugar de imponerte. Escuchás antes de decidir, y eso fortalece tu liderazgo en lugar "
            "de debilitarlo."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés ponerte a la defensiva y endurecerte con tus "
            "compañeros. Ahí ayuda frenar un momento antes de reaccionar, y compartir qué es lo "
            "que te está pesando."
        ),
    },
    (9, AccountType.INDIVIDUAL): {
        "strengths": [
            "Escuchás sin juzgar.",
            "Entendés puntos de vista muy distintos.",
            "Calmás los ánimos en un conflicto.",
            "Sos constante y paciente.",
        ],
        "tensions": [
            "Podés postergar lo que realmente te importa.",
            "Te cuesta decir lo que querés.",
            "Cedés para no generar conflictos.",
            "Te cuesta poner prioridades.",
        ],
        "growth": (
            "En tu mejor versión, te hacés lugar a vos mismo: decís lo que pensás y avanzás con lo "
            "que querés, sin perder la calma que te caracteriza. Eso no te aleja de los demás, al "
            "contrario."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés desconectarte y dejar pasar las cosas en lugar de "
            "enfrentarlas. Ahí ayuda preguntarte, aunque sea de a poco, qué es lo que de verdad "
            "querés hacer."
        ),
    },
    (9, AccountType.SALUD): {
        "strengths": [
            "Escuchás sin juzgar, algo muy valioso en este proceso.",
            "Te adaptás con calma a lo que vaya surgiendo.",
            "Transmitís una tranquilidad que ayuda en los momentos difíciles.",
            "Sos constante con lo que te propongas.",
        ],
        "tensions": [
            "Podés postergar lo que te importa, incluso en este acompañamiento.",
            "Te cuesta decir lo que realmente querés o necesitás.",
            "Cedés para evitar el conflicto, también acá.",
            "Te cuesta poner en primer lugar lo que a vos te hace bien.",
        ],
        "growth": (
            "En este acompañamiento, podés ir animándote a decir lo que pensás y lo que "
            "necesitás, sin perder tu calma habitual. Tu profesional de salud puede ayudarte a "
            "darle lugar a tu propia voz."
        ),
        "stress": (
            "Cuando te sentís sobrepasado, podés desconectarte y dejar pasar lo que te pasa en "
            "lugar de hablarlo. Nombrarlo en el espacio de acompañamiento, aunque sea despacio, ya "
            "es un avance."
        ),
    },
    (9, AccountType.RRHH): {
        "strengths": [
            "Escuchás sin juzgar y eso ayuda al clima del equipo.",
            "Ayudás a que el equipo llegue a acuerdos.",
            "Transmitís calma en los momentos de tensión en el trabajo.",
            "Sos constante y confiable en lo que hacés.",
        ],
        "tensions": [
            "Podés postergar lo que te importa a vos dentro del equipo.",
            "Te cuesta decir lo que pensás en una reunión.",
            "Cedés para no generar conflicto con tus compañeros.",
            "Te cuesta poner prioridades entre tantas tareas.",
        ],
        "growth": (
            "En tu mejor versión dentro del equipo, te animás a decir lo que pensás y a defender "
            "tus propias prioridades, sin perder la calma que aportás al grupo. Eso suma, no "
            "resta, a tu lugar en el equipo."
        ),
        "stress": (
            "Bajo presión en el trabajo, podés desconectarte y dejar que las cosas pasen en lugar "
            "de ponerles un límite. Ahí ayuda nombrar lo que te está costando, aunque sea con "
            "alguien de confianza en el equipo."
        ),
    },
}
