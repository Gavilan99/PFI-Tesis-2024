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

**Parcial (Etapa 4).** Landing → `/registro` (1 click, CTA "Empezar gratis") → completar el
formulario (tipeo, no cuenta) → "Crear cuenta" (2do click) → confirmación → "Ir a mi cuenta"
(3er click) → `/inicio`. Llega exactamente a 3 clicks, en el límite. Falta cerrar el tramo
`/inicio` → primera pregunta real del test, que hoy es un placeholder — se termina de auditar
en la Etapa 5.

### Login → primera pregunta del test

**Parcial (Etapa 4).** Post-ingreso, el login manda directo a `/inicio` (0 clicks extra —
no hay pantalla de confirmación intermedia, a diferencia del registro). Falta el tramo
`/inicio` → primera pregunta real, igual que la fila de arriba — se cierra en la Etapa 5.

### El resto

Sin auditar todavía — las rutas de test/resultados siguen siendo placeholders (Etapas 5-6).

## Cómo se audita

Cuando una pantalla deja de ser placeholder, se cuenta el click real (no el navegable-en-teoría)
y se anota acá qué etapa la cerró y si cumple el objetivo.
