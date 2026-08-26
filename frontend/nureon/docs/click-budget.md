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

## Cómo se audita

Cuando una pantalla deja de ser placeholder, se cuenta el click real (no el navegable-en-teoría)
y se anota acá qué etapa la cerró y si cumple el objetivo. Ninguna fila está auditada todavía —
las rutas de la Etapa 2 son placeholders sin flujo de clicks real.
