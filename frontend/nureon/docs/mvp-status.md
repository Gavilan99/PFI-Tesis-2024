# Qué está vivo (Etapa 9)

Estado real de cada pantalla al cierre del rediseño visual: qué pega contra `MockApiService`
(datos en memoria + `localStorage` del navegador, nada persiste en un servidor) y qué contra un
backend real. Ver `HttpApiService` (`core/services/http-api.service.ts`): **los catorce métodos
de `ApiService` están 100% sin implementar** — cada uno tira
`Error: <método>() is not implemented yet — backend integration is a later stage` a propósito.
`environment.ts` (producción) tiene `useMockApi: false` apuntando a `https://api.nureon.ai`
(no existe), así que **el build de producción de hoy no puede completar ningún flujo
interactivo** — solo sirve para validar SSR/prerender de las rutas públicas estáticas
(ver `browser-check.md`, punto 1). Todo lo que sigue corre contra `ng serve` + `MockApiService`.

## Pantalla por pantalla

### Landing (`/`)
100% estático, sin llamadas a API. Listo para producción tal cual.

### Registro (`/registro`) — CU001, RF01
`AuthService.register()` → `MockApiService.register()`. Guarda el usuario en el estado mock y
en `localStorage` (`nureon_mock_auth_user`) para sobrevivir un reload. **Real backend: 0%** —
sin Cognito, sin validación de servidor, sin persistencia en RDS.

### Ingresar (`/ingresar`) — CU002, RF02, RNF09
`AuthService.login()` → `MockApiService.login()`, misma persistencia que registro. Los botones
"Continuar con Google/Facebook" son una ranura visual inerte — sin `(click)`, comentados en el
propio HTML como `Ranura RNF09: dibujados pero inertes hasta que Cognito exista`. **Real backend:
0%.**

### `/inicio`
Sigue siendo el placeholder de la Etapa 2 ("Ruta en construcción"). Nunca se conectó — el tramo
`/inicio` → primera pregunta del test quedó pendiente desde `docs/click-budget.md` (Etapas 4/5) y
sigue así. Hoy se llega al test navegando directo a `/test`, no hay CTA en `/inicio`.

### El test (`/test`) — CU003, RF03
`createTestAttempt` / `getQuestions` / `submitResponse` / `completeTestAttempt` → todo
`MockApiService`. Auto-advance, progreso, teclado y ARIA (`radiogroup`/`radio`) funcionan sobre
datos mock. **Contenido de los ítems: placeholder explícito.** `assets/mock/questions.sample.json`
trae su propio warning: *"CONTENIDO DE RELLENO. No son ítems del banco v1 ni de ningún instrumento
real (...) Regenerar con --csv apenas esté disponible el CSV del banco v1."* El banco real de 200
ítems (`NureonAI Question Bank v1`) todavía no está cargado en el frontend. **Real backend: 0%,
y además contenido real pendiente** (dos cosas distintas: la próxima etapa que conecte un backend
real igual va a necesitar el CSV real para que el test tenga sentido).

### Resultados (`/resultados`, `/resultados/:attemptId`) — CU004, RF04, RF05, RF08
`getResult` / `getAttempt` / `getAttemptHistory` → `MockApiService`. El diagrama de eneagrama,
motivación, fortalezas/tensiones/alas se renderizan con contenido real **pero provisorio**:
`eneatype-content.ts` está marcado `isPlaceholder: true` en los 9 eneatipos, con este comentario
en el propio archivo: *"PROVISIONAL — adaptado y traducido de `type_*.txt` (...) No es la
redacción final del contenido de resultados."* Es decir, no es texto de relleno tipo lorem ipsum
— es una traducción real de las fuentes de la tesis, pendiente de una redacción final en español.
La UI marca esto explícitamente en pantalla con "Contenido de ejemplo — texto final pendiente de
redacción."

**Freemium (RF09/RF10):** el gate visual (blur + botón "Desbloquear mi perfil completo") es puro
CSS condicionado por `tier` del intento — en el mock, todo intento nace con
`tier: 'free_reduced'` hardcodeado, no hay forma de pasar a `paid_full` desde la UI. El botón
"Desbloquear..." no tiene `(click)` — es decorativo. **Mercado Pago: 0% conectado**, ni SDK ni
flujo de checkout.

### Perfil (`/perfil`) — RF06, RF07, RF08
`updateProfile` / `getAttemptHistory` / `submitFeedback` → `MockApiService`. Edición de datos,
historial de intentos y el formulario de feedback (RF06) funcionan de punta a punta contra el
mock, con estados de carga/error conectados (Etapa 8). **Real backend: 0%.**

### Styleguide (`/styleguide`)
Ruta dev-only (`!environment.production`), no existe en el build de producción ni en las rutas
prerenderizadas — confirmado en `app-routing.module.ts`. Es la lámina de sistema de diseño usada
para el material visual de esta etapa, no una pantalla de producto.

## Resumen para la defensa

| Área | Estado |
|---|---|
| UI / diseño / accesibilidad / responsive | Completo (Etapas 1-8) |
| Lógica de negocio de cada pantalla | Completa, corriendo contra `MockApiService` |
| Backend real (Flask/RDS) | 0% — `HttpApiService` es un scaffold vacío que tira error a propósito |
| Auth real (Cognito, incl. Google/Facebook) | 0% — ranura visual únicamente |
| Pagos reales (Mercado Pago, RF09/10) | 0% — gate freemium es solo CSS sobre un flag hardcodeado |
| Banco de preguntas real (200 ítems) | 0% — el test usa `questions.sample.json`, contenido de relleno declarado |
| Contenido descriptivo de eneatipos | Traducido de las fuentes de la tesis, pendiente de redacción final (no relleno) |
| `/inicio` | Placeholder de Etapa 2, sin cerrar desde entonces |

`redesign/frontend` queda listo para mergear a `master` en lo visual/UX; lo que sigue después del
merge es reemplazar `HttpApiService` por una implementación real contra el backend que responda
los contratos de la Etapa 2, más Cognito y Mercado Pago.
