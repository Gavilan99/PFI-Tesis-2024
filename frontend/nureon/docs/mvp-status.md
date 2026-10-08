# Qué está vivo (actualizado en la Feature 7 del backend)

Estado real de cada pantalla: qué pega contra el backend real (Flask + PostgreSQL + Cognito) y qué
sigue siendo provisorio. Desde la Feature 7 del backend, `HttpApiService`
(`core/services/http-api.service.ts`) implementa **los catorce métodos de `ApiService`** contra
`environment.apiBaseUrl`, y CU001 a CU004 se recorrieron de punta a punta en el navegador contra el
backend local, con Postgres y Cognito reales. Ningún componente cambió para eso: el cambio fue el
provider de `API_SERVICE`, más el manejo del token (`core/auth/`). Detalle del lado del servidor en
`backend/docs/backend-status.md`; contrato en `backend/docs/api-contract.md`.

Qué build usa qué:

| Build | `ApiService` | Para qué |
|---|---|---|
| `ng serve` (development) | `HttpApiService` → `http://localhost:5000` | Desarrollo contra el backend local |
| `npm run build` (production) | `HttpApiService` → `https://api.nureon.ai` | **No completa ningún flujo:** ese dominio no existe hasta la Feature 8 (despliegue). Sirve para validar SSR/prerender |
| `npm run build:demo` | `MockApiService` | El respaldo de la defensa: completa el recorrido entero sin backend. Sin cambios desde la Etapa 10 |

**Sesión.** El backend devuelve un access token al registrarse o ingresar. `HttpApiService` lo guarda
en `localStorage` (`nureon_access_token`), al lado del usuario que guarda `AuthService`, y un
interceptor lo manda sólo a los pedidos al backend. Se borra al cerrar sesión, y ante un 401, que
además cierra la sesión. Dura una hora y no hay refresh: al vencer, se vuelve a ingresar. Nada de
esto corre en SSR/prerender.

## Pantalla por pantalla

### Landing (`/`)
100% estático, sin llamadas a API. Listo para producción tal cual.

### Registro (`/registro`) — CU001, RF01
`AuthService.register()` → `POST /api/auth/register`. Crea la cuenta en Cognito y la fila en
`users`. Los errores del backend ("Ese email ya está registrado.", contraseña rechazada) se muestran
en el formulario tal cual llegan. La confirmación manda directo a `/test`. **Real backend: 100%.**
**El email no se verifica**: la cuenta se auto-confirma (decisión del plan del backend).

### Ingresar (`/ingresar`) — CU002, RF02, RNF09
`AuthService.login()` → `POST /api/auth/login`. "Email o contraseña incorrectos." llega del backend y
se muestra en el formulario. Los botones "Continuar con Google/Facebook" siguen siendo una ranura
visual inerte. **Real backend: 100% para email y contraseña; 0% para Google/Facebook.**

### `/inicio` — RF03
Lee `getLatestAttempt` y decide la acción primaria según el estado:

- Sin intentos → "Iniciar test".
- Intento en curso → "Retomar test" + progreso (respondidas/total) + "Empezar de nuevo" (el backend
  pasa el intento anterior a `abandoned`).
- Con resultado → "Ver mi resultado" + "Hacer el test de nuevo".

**Real backend: 100%.**

### El test (`/test`) — CU003, RF03
`createTestAttempt` / `getQuestions` / `submitResponse` / `getResponses` / `completeTestAttempt` →
backend. El subset entero (20 ítems en el tier gratuito) llega en un solo pedido; cada respuesta se
guarda al elegirla. Recargar a mitad del test retoma en el mismo ítem, leyendo la base. El cliente
manda sólo el id de la opción: la clave de corrección (`group_label`, `grouping_system`) no llega al
navegador, y las opciones de escenario vienen mezcladas por intento. **Real backend: 100%.**

**Contenido de los ítems: relleno explícito.** El backend sirve la **versión 0** del cuestionario,
que dice en cada ítem "[RELLENO · versión 0] ... no es un ítem del banco v1 ni de ningún instrumento
real". El banco real (`NureonAI Question Bank v1`) entra por el script de import del backend cuando
esté su CSV. `assets/mock/questions.sample.json` sólo lo usa el build demo.

### Resultados (`/resultados`, `/resultados/:attemptId`) — CU004, RF04, RF05, RF08
`getLatestAttempt` / `getAttempt` / `getResult` → backend. El resultado se calcula y guarda al cerrar
el test. **Real backend: 100% en el circuito; el eneatipo no sale de un modelo entrenado.** Con
`CLASSIFIER_BACKEND=stub` (el de desarrollo) sale de un conteo de respuestas por grupo más la tabla
canónica: no es ML. La alternativa disponible, `legacy_tree`, es el árbol de 2024, entrenado sobre un
dataset armado por el equipo (no respuestas reales); coincide con la tabla canónica en 77 de 81
combinaciones. Los cuatro Random Forest nuevos todavía no existen. Ninguna probabilidad, grupo ni
margen llega al navegador.

El contenido de motivación/fortalezas/tensiones/alas es real **pero provisorio**:
`eneatype-content.ts` está marcado `isPlaceholder: true` en los 9 eneatipos (traducción de las
fuentes de la tesis, pendiente de redacción final), y la UI lo dice en pantalla.

**Freemium (RF09/RF10):** el `tier` del intento lo decide el servidor (hoy siempre `free_reduced`; la
Feature 6 lo resuelve por suscripción). Pero **el texto premium viaja en el bundle**: "En crecimiento
y bajo estrés" está en `eneatype-content.ts` y se difumina con CSS, así que quien abra devtools lo
lee. El botón "Desbloquear mi perfil completo" abre `FreemiumInfoDialogComponent`, que dice que el
pago está en desarrollo. **Mercado Pago: 0% conectado.**

### Perfil (`/perfil`) — RF06, RF07, RF08
`updateProfile` / `getAttemptHistory` / `getResult` / `submitFeedback` → backend. Edición de datos,
historial de intentos con su eneatipo y el formulario de comentarios funcionan contra la base.
**Real backend: 100%.** El borrado de cuenta existe en el backend (`DELETE /api/users/me`) pero no
tiene pantalla.

### Sobre el eneagrama (`/eneagrama`) — Etapa 10
Contenido educativo estático. Nombra las cuatro familias de triadas sin publicar qué ítem u opción
corresponde a cada una. Sin llamadas a API.

### Nosotros (`/nosotros`) — Etapa 10
Borrador. La sección "Autores" es un placeholder explícito en pantalla
(`[Nombre del autor/a — confirmar]`). **Pendiente: que confirmes nombres, roles y una bio breve.**

### Contacto (`/contacto`) — Etapa 10
`submitContactMessage` → `POST /api/contact-messages`, sin sesión. El backend no lo guarda: lo manda
por mail con Amazon SES. **Real backend: 100%, con SES provisorio**: en modo sandbox, a una casilla
provisoria de Gmail, y sólo llega a direcciones verificadas. En desarrollo el backend corre con
`MAIL_SENDER=local`, que no manda nada.

### Styleguide (`/styleguide`)
Ruta dev-only (`!environment.production`): no está en las rutas del build de producción ni del demo,
ni en las prerenderizadas.

## Errores y límites que el frontend no conoce

El backend rechaza nombre de contacto de más de 100 caracteres, email de más de 254, mensaje de más
de 5.000 y comentario de más de 2.000. Los formularios no tienen esos máximos: pasarse muestra el
error genérico del formulario ("No pudimos enviar tu mensaje/comentario. Probá de nuevo."), legible,
y el formulario sigue usable (verificado en la Feature 7). Agregar los máximos en pantalla es una
tarea aparte.

Al cerrar sesión, la pantalla actual no se va: en `/perfil`, los datos de la cuenta siguen visibles
hasta navegar (el token y el usuario ya no están). Es un cambio de componente, fuera de la Feature 7.

## Presupuesto de clicks (`docs/click-budget.md`)

Recontado en la Feature 7, contra el backend real (no empeoró ninguno):

| Recorrido | Objetivo | Contado |
|---|---|---|
| Landing → primera pregunta (usuario nuevo) | ≤ 3 | **3**: "Empezar gratis", "Crear cuenta", "Empezar el test" |
| Login → primera pregunta | ≤ 2 post-ingreso | **1**: login → `/inicio` (0) → "Iniciar test" |
| Responder el test completo | 1 por ítem | **20 clicks para 20 ítems**, sin "Siguiente" |
| Fin del test → resultado | 1 | **1**: "Ver mi resultado" |
| Entrar a la app → resultado anterior | 1 | **1**: login → `/inicio` → "Ver mi resultado" |

## Resumen para la defensa

| Área | Estado |
|---|---|
| UI / diseño / accesibilidad / responsive | Completo (Etapas 1-8) |
| Recorrido de punta a punta sin placeholders de UI | Completo (Etapa 10) |
| Backend real (Flask/PostgreSQL), las catorce operaciones | Completo y verificado en local (Feature 7) |
| Auth real con email y contraseña (Cognito) | Completo. Sin verificación de email ni recuperación de contraseña |
| Auth con Google/Facebook (RNF09) | 0% — ranura visual únicamente |
| Clasificación | `stub` (conteo, no ML) o `legacy_tree` (árbol de 2024 sobre dataset armado). Modelo entrenado: 0% |
| Banco de preguntas real | 0% — se sirve el relleno, versión 0 |
| Contenido descriptivo de eneatipos | Traducido de las fuentes de la tesis, pendiente de redacción final |
| Freemium | Tier del lado del servidor; el texto premium igual viaja en el bundle |
| Pagos reales (Mercado Pago, RF09/10) | 0% — Feature 6 postergada |
| Despliegue (S3/CloudFront, ECS, RDS) | 0% — Feature 8 postergada; todo corre local |
| Build desplegable sin backend (`build:demo`) | Completo, sin cambios: el respaldo de la defensa |
| Bios de autores en `/nosotros` | Pendiente de que las confirmes — marcado en pantalla |
