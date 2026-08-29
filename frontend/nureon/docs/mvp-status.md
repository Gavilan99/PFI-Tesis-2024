# Qué está vivo (actualizado en Etapa 10)

Estado real de cada pantalla al cierre del rediseño visual: qué pega contra `MockApiService`
(datos en memoria + `localStorage` del navegador, nada persiste en un servidor) y qué contra un
backend real. Ver `HttpApiService` (`core/services/http-api.service.ts`): **los quince métodos
de `ApiService` están 100% sin implementar** — cada uno tira
`Error: <método>() is not implemented yet — backend integration is a later stage` a propósito.
`environment.ts` (producción) tiene `useMockApi: false` apuntando a `https://api.nureon.ai`
(no existe), así que **el build de producción de hoy no puede completar ningún flujo
interactivo** — solo sirve para validar SSR/prerender de las rutas públicas estáticas
(ver `browser-check.md`).

**Etapa 10 agrega `environment.demo.ts` (`npm run build:demo`)**: mismo build optimizado, pero
`useMockApi: true`, así que sí completa el recorrido entero — es lo que se sube a S3 para mostrar
el producto sin depender de un backend real ni de `ng serve`.

## Pantalla por pantalla

### Landing (`/`)
100% estático, sin llamadas a API. Listo para producción tal cual.

### Registro (`/registro`) — CU001, RF01
`AuthService.register()` → `MockApiService.register()`. Guarda el usuario en el estado mock y
en `localStorage` (`nureon_mock_auth_user`) para sobrevivir un reload. La confirmación manda
directo a `/test` (Etapa 10 — antes mandaba a `/inicio`, lo que rompía el presupuesto de
`docs/click-budget.md`; ver ese doc). **Real backend: 0%** — sin Cognito, sin validación de
servidor, sin persistencia en RDS.

### Ingresar (`/ingresar`) — CU002, RF02, RNF09
`AuthService.login()` → `MockApiService.login()`, misma persistencia que registro. Los botones
"Continuar con Google/Facebook" son una ranura visual inerte — sin `(click)`, comentados en el
propio HTML como `Ranura RNF09: dibujados pero inertes hasta que Cognito exista`. **Real backend:
0%.**

### `/inicio` — Etapa 10, RF03
Ya no es el placeholder de la Etapa 2 — es el punto de partida real de la sesión. Lee
`getLatestAttempt(userId)` y decide la acción primaria según el estado:

- Sin intentos → "Iniciar test".
- Intento en curso → "Retomar test" + progreso (`getQuestions`/`getResponses` para el conteo
  respondidas/total) + "Empezar de nuevo" (crea un intento nuevo, que pasa a ser el "latest").
- Con resultado → "Ver mi resultado" + "Hacer el test de nuevo".

Todo contra `MockApiService`. **Real backend: 0%.**

### El test (`/test`) — CU003, RF03
`createTestAttempt` / `getQuestions` / `submitResponse` / `completeTestAttempt` → todo
`MockApiService`. Auto-advance, progreso, teclado y ARIA (`radiogroup`/`radio`) funcionan sobre
datos mock. Desde Etapa 10 el footer no se muestra en esta ruta (`AppComponent.showFooter$`) y la
pregunta se centra verticalmente en vez de quedar pegada arriba con un hueco muerto abajo.

**Contenido de los ítems: placeholder explícito.** `assets/mock/questions.sample.json` trae su
propio warning: *"CONTENIDO DE RELLENO. No son ítems del banco v1 ni de ningún instrumento real
(...) Regenerar con --csv apenas esté disponible el CSV del banco v1."* El banco real de 200
ítems (`NureonAI Question Bank v1`) todavía no está cargado en el frontend. **Real backend: 0%,
y además contenido real pendiente.**

### Resultados (`/resultados`, `/resultados/:attemptId`) — CU004, RF04, RF05, RF08
`getResult` / `getAttempt` / `getAttemptHistory` → `MockApiService`. Desde Etapa 10, el diagrama
y el título/resumen/motivación comparten fila en desktop (antes el diagrama dejaba una columna
vacía mientras el resto del contenido seguía abajo en una sola columna — ver
`docs/screenshots/06-resultados-desktop.jpg` de Etapa 9 contra la versión actual).

El contenido de motivación/fortalezas/tensiones/alas es real **pero provisorio**:
`eneatype-content.ts` está marcado `isPlaceholder: true` en los 9 eneatipos, con este comentario
en el propio archivo: *"PROVISIONAL — adaptado y traducido de `type_*.txt` (...) No es la
redacción final del contenido de resultados."* Es decir, no es texto de relleno tipo lorem ipsum
— es una traducción real de las fuentes de la tesis, pendiente de una redacción final en español.
La UI lo marca explícitamente en pantalla con "Contenido de ejemplo — texto final pendiente de
redacción."

**Freemium (RF09/RF10):** el gate visual (blur + botón "Desbloquear mi perfil completo") es puro
CSS condicionado por `tier` del intento — en el mock, todo intento nace con
`tier: 'free_reduced'` hardcodeado, no hay forma de pasar a `paid_full` desde la UI. Desde
Etapa 10, el botón abre `FreemiumInfoDialogComponent`: un panel honesto con los dos niveles
(gratis/pago) y una nota explícita de que el flujo de pago está en desarrollo — no desbloquea
nada ni simula un pago. **Mercado Pago: 0% conectado**, ni SDK ni flujo de checkout.

### Perfil (`/perfil`) — RF06, RF07, RF08
`updateProfile` / `getAttemptHistory` / `submitFeedback` → `MockApiService`. Edición de datos,
historial de intentos y el formulario de feedback (RF06) funcionan de punta a punta contra el
mock, con estados de carga/error conectados (Etapa 8). **Real backend: 0%.**

### Sobre el eneagrama (`/eneagrama`) — Etapa 10
Contenido educativo estático: qué es el eneagrama, los 9 tipos (solo nombres — la copy
descriptiva completa vive en `resultados/eneatype-content.ts` y es provisoria, así que esta
página no depende de ella), y qué distingue a NureonAI. Nombra las cuatro familias de triadas
(Centros de Inteligencia, Horneviano, Armónico, Relaciones Objetales) sin publicar qué ítem u
opción corresponde a cada una — es la clave de corrección del instrumento. Sin llamadas a API.

### Nosotros (`/nosotros`) — Etapa 10
Borrador. El párrafo sobre el proyecto está escrito; la sección "Autores" es un placeholder
explícito en pantalla (`[Nombre del autor/a — confirmar]`) — no se inventaron datos biográficos.
**Pendiente: que confirmes nombres, roles y una bio breve antes de sacar el aviso de borrador.**

### Contacto (`/contacto`) — Etapa 10
Formulario simple (nombre, email, mensaje) → `MockApiService.submitContactMessage()`, agregado en
esta etapa junto con el resto de `ApiService` (no existía antes; no hay tabla `contact_messages`
en el PDR — es una conveniencia del mock, igual que `submitFeedback`). Mismos estados de
carga/error que el resto de los formularios. **Real backend: 0%** — nadie recibe estos mensajes
todavía.

### Styleguide (`/styleguide`)
Ruta dev-only (`!environment.production`), no existe en el build de producción ni en el build
demo ni en las rutas prerenderizadas — confirmado en `app-routing.module.ts`. Es la lámina de
sistema de diseño usada para el material visual, no una pantalla de producto.

## Presupuesto de clicks (`docs/click-budget.md`)

Cerrado en esta etapa:

- **Landing → primera pregunta (usuario nuevo), ≤ 3 clicks**: "Empezar gratis" (1) → "Crear
  cuenta" (2) → "Empezar el test" en la confirmación (3, manda directo a `/test`, ya no a
  `/inicio`). **Cumple, justo en el límite.**
- **Login → primera pregunta, ≤ 2 clicks post-ingreso**: login manda a `/inicio` (0 extra) →
  "Iniciar test"/"Retomar test" (1). **Cumple.**
- **Responder el test completo, 1 click por ítem**: sin cambios, ya cumplía.
- **Fin del test → resultado, 1 click**: sin cambios, ya cumplía.
- **Entrar a la app → ver resultado anterior, 1 click**: `/inicio` con estado "completado" →
  "Ver mi resultado" (1). **Cumple** — antes no había forma de auditar esto porque `/inicio` no
  existía.

## Resumen para la defensa

| Área | Estado |
|---|---|
| UI / diseño / accesibilidad / responsive | Completo (Etapas 1-8) |
| Recorrido de punta a punta sin placeholders | Completo (Etapa 10) |
| Lógica de negocio de cada pantalla | Completa, corriendo contra `MockApiService` |
| Build desplegable sin backend (`build:demo`) | Completo (Etapa 10) |
| Backend real (Flask/RDS) | 0% — `HttpApiService` es un scaffold vacío que tira error a propósito |
| Auth real (Cognito, incl. Google/Facebook) | 0% — ranura visual únicamente |
| Pagos reales (Mercado Pago, RF09/10) | 0% — el panel freemium es honesto sobre esto |
| Banco de preguntas real (200 ítems) | 0% — el test usa `questions.sample.json`, contenido de relleno declarado |
| Contenido descriptivo de eneatipos | Traducido de las fuentes de la tesis, pendiente de redacción final (no relleno) |
| Bios de autores en `/nosotros` | Pendiente de que las confirmes — marcado en pantalla |

`redesign/frontend` queda listo para mergear a `master` en lo visual/UX. Lo que sigue después del
merge es reemplazar `HttpApiService` por una implementación real contra el backend que responda
los contratos de la Etapa 2, más Cognito y Mercado Pago — y cargar el banco de preguntas real.
