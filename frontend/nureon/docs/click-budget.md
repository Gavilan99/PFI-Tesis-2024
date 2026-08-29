# Presupuesto de clicks (RNF10)

Objetivo verificable para "completar el test y acceder a resultados con mínimo de clicks".
Cada fila es un recorrido completo, no un paso aislado — se audita etapa por etapa a medida
que las pantallas reales (Etapas 4-6) reemplazan los placeholders de la Etapa 2.

| Recorrido | Objetivo |
|---|---|
| Landing → primera pregunta del test (usuario nuevo) | ≤ 3 clicks |
| Login → primera pregunta del test | ≤ 2 clicks post-ingreso |
| Responder el test completo | 1 click por ítem, sin botón "Siguiente" |
| Fin del test → resultado en pantalla | 1 click |
| Entrar a la app → ver resultado anterior | 1 click |

## Auditoría

### Landing → primera pregunta del test (usuario nuevo)

**Cerrado (Etapa 10).** Landing → `/registro` (1 click, CTA "Empezar gratis") → completar el
formulario (tipeo, no cuenta) → "Crear cuenta" (2do click) → confirmación → "Empezar el test"
(3er click) → `/test`, primera pregunta. Llega exactamente a 3 clicks, en el límite.

Hasta Etapa 9 el botón de confirmación mandaba a `/inicio` en vez de `/test` — una vez que
`/inicio` dejó de ser placeholder y ganó su propio botón "Iniciar test" (Etapa 10), ese hop
extra hubiera sumado un 4to click y roto el presupuesto. Se resolvió mandando la confirmación
del registro directo a `/test`: para una cuenta recién creada (sin intentos) el destino es
idéntico al que ofrecería `/inicio` de todas formas, solo que sin el paso intermedio.

### Login → primera pregunta del test

**Cerrado (Etapa 10).** Post-ingreso, el login manda directo a `/inicio` (0 clicks extra) →
"Iniciar test" o "Retomar test" según el estado (1 click) → primera pregunta (o la pregunta
donde había quedado, si el intento estaba en curso). Cumple el objetivo de ≤ 2 clicks
post-ingreso con margen.

### Responder el test completo

**Cumple, sin cambios.** 1 click (o 1 tecla) por ítem, auto-advance, sin botón "Siguiente" —
así desde la Etapa 5.

### Fin del test → resultado en pantalla

**Cumple, sin cambios.** "Ver mi resultado" en la pantalla de cierre del test, 1 click — así
desde la Etapa 6.

### Entrar a la app → ver resultado anterior

**Cerrado (Etapa 10).** No se podía auditar hasta que `/inicio` existiera de verdad: una cuenta
con un intento completado entra a `/inicio` y ve "Ver mi resultado" como acción primaria — 1
click. `/inicio` clasifica el estado leyendo `getLatestAttempt`, la misma lógica que
`UserJourneyStateService` ya modelaba desde la Etapa 2.

## Cómo se audita

Cuando una pantalla deja de ser placeholder, se cuenta el click real (no el navegable-en-teoría)
y se anota acá qué etapa la cerró y si cumple el objetivo.
