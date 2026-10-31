# Contrato de la API

Las formas de datos salen de `frontend/nureon/src/app/core/models/`. El JSON va en camelCase. Todo
error tiene la misma forma:

```json
{"error": {"code": "SNAKE_CASE_IN_ENGLISH", "message": "Texto en español."}}
```

`message` se muestra tal cual: `HttpApiService` lo convierte en el `Error` con el que rechaza cada
método. Si no llega ese cuerpo (el servidor no responde, o responde otra cosa), el `Error` lleva un
mensaje genérico en español.

**Verificado automáticamente** (`tests/test_contract.py`): para cada una de las quince rutas de la
tabla de abajo, el conjunto de claves de la respuesta es *igual* al de la interfaz TypeScript con la
que el frontend la lee. Para el registro también el cuerpo: los campos que acepta el backend son las
claves de `RegisterInput` (`auth.model.ts`). Las claves esperadas no están copiadas en el test: se leen de los `.ts` del
frontend, así que un campo agregado o sacado de cualquiera de los dos lados lo rompe. Lo mismo para
las dos rutas de los cortes (Feature 9), con su método en `ApiService` desde la Feature 10
(`continueTestAttempt` y `getCutStatus`), en un test aparte porque necesitan el tier pago: ver
[Feature 9](#feature-9-cortes-fijos). Y para las tres rutas de pagos (Feature 6: `getSubscription`,
`startCheckout`, `confirmPayment`, en `subscription.model.ts`), en otro test aparte con la pasarela
local: ver [Feature 6](#feature-6-pagos-con-mercado-pago). `getPersonalizedDescription` (Feature 17,
también necesita el tier pago) tiene el suyo: ver [Feature 17](#feature-17-descripción-personalizada).

## Las quince rutas y `HttpApiService`

| Método de `ApiService` | Ruta | Respuesta | Qué hace `HttpApiService` además de la llamada |
|---|---|---|---|
| `register` | `POST /api/auth/register` | `201` `{user, accessToken, expiresIn}` | Guarda el token; devuelve `user` |
| `login` | `POST /api/auth/login` | `200` `{user, accessToken, expiresIn}` | Guarda el token; devuelve `user` |
| `updateProfile` | `PATCH /api/users/me` | `200` `User` | No manda el `userId` |
| `deleteAccount` | `DELETE /api/users/me` | `204` sin cuerpo | Devuelve `void`; no manda el `userId` |
| `createTestAttempt` | `POST /api/attempts` | `201` `TestAttempt` | Sin cuerpo; no manda el `userId` |
| `getQuestions` | `GET /api/attempts/{id}/questions` | `200` `Question[]` | — |
| `submitResponse` | `POST /api/attempts/{id}/responses` | `200` `TestResponse` | Manda exactamente los cuatro campos |
| `getResponses` | `GET /api/attempts/{id}/responses` | `200` `TestResponse[]` | — |
| `completeTestAttempt` | `POST /api/attempts/{id}/complete` | `200` `TestAttempt` | Sin cuerpo |
| `getLatestAttempt` | `GET /api/attempts/latest` | `200` `TestAttempt` o `null` | No manda el `userId` |
| `getAttempt` | `GET /api/attempts/{id}` | `200` `TestAttempt` | Un `404` se devuelve como `null` |
| `getAttemptHistory` | `GET /api/attempts` | `200` `TestAttempt[]` | No manda el `userId` |
| `getResult` | `GET /api/attempts/{id}/result` | `200` `Result` | — |
| `submitFeedback` | `POST /api/feedback` | `204` sin cuerpo | Devuelve `void` |
| `submitContactMessage` | `POST /api/contact-messages` | `204` sin cuerpo | Devuelve `void`; va sin token |

El `userId` que el contrato pide en algunos métodos se sigue recibiendo y no se manda: la identidad
sale del token.

El token se guarda en `localStorage` (`nureon_access_token`, con su vencimiento), al lado del usuario
que ya guarda `AuthService`, y lo agrega un interceptor (`core/auth/`) sólo a los pedidos a
`environment.apiBaseUrl`. Se borra cuando `AuthService` se queda sin usuario (cerrar sesión) y cuando el
backend responde `401` a una ruta que no es de `/api/auth/`; en ese caso además se cierra la sesión,
para que la app no quede "logueada" con un token que ya no sirve. Si al arrancar hay usuario guardado
pero ningún token vigente, también se cierra la sesión. Nada de esto corre en el render del servidor
(SSR/prerender).

## Autenticación

Toda ruta exige `Authorization: Bearer <accessToken>`, salvo `GET /api/health`,
`GET /api/health/ready`, `POST /api/auth/register`, `POST /api/auth/login` y
`POST /api/contact-messages`. Se acepta sólo el access
token del user pool configurado: se verifican la firma, el emisor, el `client_id`, el vencimiento y
`token_use = access`. Un token ausente, vencido, mal firmado o de otro pool responde
`401 UNAUTHORIZED`. La identidad sale del token y de ningún otro lado.

Toda ruta autenticada puede responder, además de lo que diga su tabla:

| Status | `code` | `message` |
|---|---|---|
| 401 | `UNAUTHORIZED` | No se pudo autenticar la solicitud. |
| 401 | `ACCOUNT_NOT_ENABLED` | Esta cuenta no está habilitada en NureonAI. Registrate con otro email. |
| 503 | `IDENTITY_UNAVAILABLE` | El servicio de cuentas no está disponible. Probá de nuevo en unos minutos. |

El 503 es no poder bajar las claves públicas del user pool para verificar la firma.
`ACCOUNT_NOT_ENABLED` es sólo de producción: ver el login.

Y cualquier ruta, pública o no:

| Status | `code` | `message` |
|---|---|---|
| 404 | `NOT_FOUND` | El recurso solicitado no existe. (Ruta inexistente, o un `{id}` que no es un UUID.) |
| 405 | `METHOD_NOT_ALLOWED` | El método no está permitido para este recurso. |
| 500 | `INTERNAL_SERVER_ERROR` | Ocurrió un error interno. |

Un cuerpo que no es JSON válido, o no es un objeto, responde `400 VALIDATION_ERROR`, como cualquier otro
cuerpo inválido.

`User` (igual a `user.model.ts`):

```json
{
  "id": "uuid",
  "displayName": "string",
  "email": "string",
  "accountType": "individual | rrhh | salud | null",
  "ageRange": "string | null",
  "gender": "string | null",
  "country": "string | null",
  "professionContext": "string | null"
}
```

## Feature 2: cuentas

### `POST /api/auth/register` — `register(input)`

Cuerpo: exactamente `RegisterInput`, `{"username", "email", "password", "consentAccepted"}`.
`username` de 3 a 255 caracteres; `password` de 8 a 256. El email se guarda en minúsculas. La cuenta
queda confirmada al crearse: no hay verificación de email.

`consentAccepted` (Feature 11) es la casilla «Leí y acepto la Política de privacidad y los Términos y
condiciones, y consiento que mis datos se guarden en Estados Unidos» (Ley 25.326, arts. 5, 6 y 12;
decreto 1558/2001). Tiene que ser el booleano JSON `true`: si falta o es `false`, `400
CONSENT_REQUIRED` y no se crea nada, ni en la base ni en el proveedor de identidad; si es otra cosa
(`"true"`, `1`, `null`), `400 VALIDATION_ERROR`. Un cuerpo inválido por otro motivo también es
`VALIDATION_ERROR`, venga o no el consentimiento. Al crear la cuenta el servidor guarda
`users.consent_accepted_at` (el momento del registro) y `users.consent_version`, la versión vigente
de los textos según `CONSENT_VERSION`. **El cliente no elige la versión:** un `consentVersion` en el
cuerpo es un campo de más, `400 VALIDATION_ERROR`. Ninguno de los dos sale en `User`.

`201`:

```json
{"user": User, "accessToken": "eyJ...", "expiresIn": 3600}
```

| Status | `code` | `message` |
|---|---|---|
| 400 | `CONSENT_REQUIRED` | Para crear tu cuenta tenés que aceptar la Política de privacidad y los Términos y condiciones. |
| 409 | `EMAIL_ALREADY_REGISTERED` | Ese email ya está registrado. |
| 409 | `ACCOUNT_CONFLICT` | La cuenta no se pudo asociar: ya existe otra con ese email. |
| 400 | `PASSWORD_REJECTED` | La contraseña no cumple los requisitos de seguridad. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 503 | `IDENTITY_UNAVAILABLE` | El servicio de cuentas no está disponible. Probá de nuevo en unos minutos. |

`CONSENT_REQUIRED` se evalúa antes que el email repetido: sin consentimiento no se mira nada más.
`ACCOUNT_CONFLICT` es la carrera de dos registros simultáneos con el mismo email: la cuenta recién
creada en el proveedor se borra y no queda nada a medias.

### `POST /api/auth/login` — `login(input)`

Cuerpo: exactamente `LoginInput`, `{"email", "password"}`. El email no distingue mayúsculas.
`200` con la misma forma que el registro.

| Status | `code` | `message` |
|---|---|---|
| 401 | `INVALID_CREDENTIALS` | Email o contraseña incorrectos. |
| 401 | `ACCOUNT_NOT_ENABLED` | Esta cuenta no está habilitada en NureonAI. Registrate con otro email. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 409 | `ACCOUNT_CONFLICT` | La cuenta no se pudo asociar: ya existe otra con ese email. |
| 503 | `IDENTITY_UNAVAILABLE` | El servicio de cuentas no está disponible. Probá de nuevo en unos minutos. |

Email inexistente y contraseña incorrecta responden igual, a propósito. Fuera de producción, el login
crea la fila de `users` si falta; `ACCOUNT_CONFLICT` es el caso en que esa fila choca con el email de
otra cuenta viva.

**En producción esa fila no se crea** (Feature 11): una cuenta que existe en Cognito pero no se
registró por `POST /api/auth/register` no tiene consentimiento, así que el login responde `401
ACCOUNT_NOT_ENABLED` y no crea nada. Lo mismo cualquier ruta autenticada con un token de esa cuenta. El
caso real es una cuenta de desarrollo, porque el pool de Cognito es el mismo: registrarse de nuevo con
ese email no funciona (Cognito ya lo tiene y responde `409 EMAIL_ALREADY_REGISTERED`), de ahí «con otro
email». La cuenta de Cognito no se toca.

### `GET /api/users/me`

Sin método en `ApiService`: el frontend recibe el usuario en la respuesta del login. `200` con el
`User` del token.

### `PATCH /api/users/me` — `updateProfile(userId, input)`

Cuerpo: `UpdateProfileInput`, todos opcionales: `displayName`, `accountType`, `ageRange`, `gender`,
`country`, `professionContext`. Sólo cambian los campos enviados. `null` o `""` borra un campo
opcional; `displayName` no puede quedar vacío. `accountType` se valida contra el enum. El `userId`
que pasa el frontend se ignora (si viene en el cuerpo también). `200` con el `User` actualizado.

| Status | `code` | `message` |
|---|---|---|
| 400 | `EMAIL_NOT_EDITABLE` | El email no se puede modificar. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |

### `DELETE /api/users/me` — `deleteAccount(userId)`

Desde la Feature 11 tiene pantalla: «Borrar mi cuenta» en `/perfil` (PA-7). Borrado blando con
anonimización según la tabla "Borrado de cuenta" de CLAUDE.md, y borrado del usuario en el proveedor de
identidad. **`consent_accepted_at` y `consent_version` se conservan:** son la constancia de que el
tratamiento fue lícito. `204` sin cuerpo. Después, el token viejo responde `401` y el mismo email se
puede volver a registrar. Si el proveedor falla, `503 IDENTITY_UNAVAILABLE` y no se anonimiza nada.
El `userId` del contrato no se manda.

## Feature 3: intentos

`TestAttempt` (igual a `test-attempt.model.ts`):

```json
{
  "id": "uuid",
  "userId": "uuid | null",
  "subjectId": "uuid | null",
  "tier": "free_reduced | paid_full",
  "questionnaireVersion": 0,
  "status": "in_progress | completed | abandoned",
  "startedAt": "2026-10-07T04:39:31.343081Z",
  "completedAt": "string | null"
}
```

Un intento ajeno responde igual que uno que no existe, en todos los endpoints de abajo:

| Status | `code` | `message` |
|---|---|---|
| 404 | `ATTEMPT_NOT_FOUND` | El intento no existe. |

Un `{id}` que no es un UUID responde `404 NOT_FOUND`.

### `POST /api/attempts` — `createTestAttempt(userId)`

Sin cuerpo. Si viene uno, sólo puede traer `userId`, que se ignora. El tier lo decide el servidor:
un intento nuevo es siempre `free_reduced`, también para quien paga, y pasa a `paid_full` al seguir al
corte 2 (Feature 9). Si el usuario tenía un intento `in_progress`, pasa a `abandoned` en la misma
transacción. Se usa la versión más alta con preguntas activas, y se sirve **el corte 1**: los 40 ítems
del plan de cortes, los mismos para todos y en el mismo orden (`serve_new_items` del manifest de los
modelos), guardados como filas sin responder con `displayOrder` de 1 a 40. `201` con el `TestAttempt`.

| Status | `code` | `message` |
|---|---|---|
| 400 | `TIER_NOT_ACCEPTED` | El tipo de test lo decide el servidor: no se puede elegir al crearlo. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 503 | `QUESTIONNAIRE_UNAVAILABLE` | El cuestionario no está disponible en este momento. Probá de nuevo más tarde. |

El 503 es un problema de carga del banco (no hay versión activa, o le falta algún ítem del plan de
cortes: cada código `Q007` se busca por `questions.display_order` = 7 entre las preguntas activas), no
del usuario: queda en el log como error, con los códigos que faltan. No se crea ni se abandona nada.

### `GET /api/attempts/{id}/questions` — `getQuestions(attemptId)`

`200` con **todo lo servido hasta ahora** (40, 90 o 145 ítems), en el orden del intento. Recargar
devuelve lo mismo.

```json
[
  {
    "id": "uuid",
    "questionType": "scenario | multiple_choice",
    "promptText": "string",
    "displayOrder": 1,
    "answerOptions": [
      {"id": "uuid", "questionId": "uuid", "optionText": "string", "displayOrder": 1}
    ]
  }
]
```

Nada más. `displayOrder` es la posición servida, no la del banco: de 1 a N para las preguntas y de 1
a k para las opciones. Desde la Feature 9 **todas las opciones salen en el orden del banco**, también
las de escenario: es el orden que vio el piloto con el que se entrenaron los modelos. El orden servido
se sigue guardando en `responses.option_order`. `grouping_system` y `group_label` no salen nunca.

### `POST /api/attempts/{id}/responses` — `submitResponse(attemptId, response)`

Cuerpo: exactamente `NewResponseInput`, con los cuatro campos:

```json
{"questionId": "uuid", "selectedOptionId": "uuid", "freeTextResponse": null, "orderingResponse": null}
```

`freeTextResponse` y `orderingResponse` tienen que venir en `null`. Es un upsert por pregunta:
responder otra vez reemplaza la respuesta anterior. `200` con el `TestResponse`:

```json
{
  "id": "uuid",
  "testAttemptId": "uuid",
  "questionId": "uuid",
  "selectedOptionId": "uuid",
  "freeTextResponse": null,
  "orderingResponse": null,
  "answeredAt": "2026-10-07T04:39:56.012558Z"
}
```

| Status | `code` | `message` |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 400 | `QUESTION_NOT_IN_ATTEMPT` | La pregunta no forma parte de este intento. |
| 400 | `OPTION_NOT_IN_QUESTION` | La opción elegida no corresponde a esa pregunta. |
| 409 | `ATTEMPT_NOT_IN_PROGRESS` | El intento ya no está en curso. |

### `GET /api/attempts/{id}/responses` — `getResponses(attemptId)`

`200` con los `TestResponse` ya respondidos, en el orden del intento. Las preguntas todavía sin
responder no aparecen.

### `POST /api/attempts/{id}/complete` — `completeTestAttempt(attemptId)`

Cierra el intento y calcula su resultado, en la misma transacción (Feature 4.1). Sólo con todo lo
servido respondido; cierra en el corte en que esté, y el resultado sale de los modelos de ese corte.
`200` con el `TestAttempt` en `completed`. Llamarlo otra vez devuelve lo mismo y no cambia nada: no
vuelve a clasificar ni pisa el resultado.

| Status | `code` | `message` |
|---|---|---|
| 409 | `ATTEMPT_INCOMPLETE` | Quedan preguntas sin responder: el test no se puede cerrar todavía. |
| 409 | `ATTEMPT_NOT_IN_PROGRESS` | El intento ya no está en curso. (Si está `abandoned`.) |
| 500 | `RESULT_NOT_GENERATED` | No pudimos calcular tu resultado. El test sigue abierto: probá cerrarlo de nuevo. |

El 500 es una falla del clasificador: queda en el log, y el intento sigue `in_progress` sin resultado
ni predicciones, así que se puede volver a cerrar.

### `GET /api/attempts/latest` — `getLatestAttempt(userId)`

`200` con el intento más reciente del usuario, en cualquier estado. **Sin intentos, `200` con el
cuerpo `null`**: no tener intentos no es un error, y es lo que el contrato devuelve.

### `GET /api/attempts/{id}` — `getAttempt(attemptId)`

`200` con el `TestAttempt`. Si no existe o es ajeno, `404 ATTEMPT_NOT_FOUND` (decidido el 07-10): el
`null` del contrato lo produce `HttpApiService` (Feature 7) al recibir el 404. En `/resultados`, null
y error terminan en el mismo estado de error, así que la pantalla no cambia.

### `GET /api/attempts` — `getAttemptHistory(userId)`

`200` con todos los intentos del usuario, del más nuevo al más viejo. Sin intentos, `[]`.

## Feature 4.1: resultado

`Result` (igual a `result.model.ts`):

```json
{
  "id": "uuid",
  "testAttemptId": "uuid",
  "eneatype": 9,
  "descriptionText": "string",
  "generatedAt": "2026-10-07T20:36:28.372580Z"
}
```

Nada más. Las predicciones de los cuatro clasificadores (grupo, probabilidades, versión de modelo) y
el margen de confianza se guardan y no salen nunca: ni como número, ni derivados, ni en palabras.
`descriptionText` es un texto fijo por eneatipo: el resumen de una frase del frontend.

### `GET /api/attempts/{id}/result` — `getResult(attemptId)`

`200` con el `Result` del intento, si es propio y está `completed`. Cualquier otro caso (no existe,
es ajeno, está `in_progress` o `abandoned`) responde lo mismo:

| Status | `code` | `message` |
|---|---|---|
| 404 | `RESULT_NOT_FOUND` | El resultado no existe. |

Un `{id}` que no es un UUID responde `404 NOT_FOUND`.

## Feature 17: descripción personalizada

`PersonalizedDescription` (igual a `result.model.ts`):

```json
{
  "status": "not_in_plan | profile_missing | personalized | unavailable",
  "strengths": ["string"] | null,
  "tensions": ["string"] | null,
  "growth": "string | null",
  "stress": "string | null"
}
```

### `GET /api/attempts/{id}/result/personalized` — `getPersonalizedDescription(attemptId)`

Misma regla de acceso que `getResult`, mismo `404 RESULT_NOT_FOUND`. `200` siempre, nunca un error por
el plan o el perfil:

- `not_in_plan`: el intento no es `paid_full`. Nunca llama al generador.
- `profile_missing`: es `paid_full`, pero `accountType`, `ageRange` y `professionContext` están los
  tres vacíos. Nunca llama al generador.
- `personalized`: las cuatro secciones de abajo, generadas por Amazon Bedrock a partir del eneatipo,
  `descriptionText` y esos tres campos del perfil (un solo pedido, no cuatro: el formato de la
  respuesta se pide fijo y se separa con manejo de strings). Se reusan sin volver a generar si el
  perfil y el modelo configurado no cambiaron desde la última vez. `strengths` y `tensions` son listas
  de 3 a 6 frases cada una; `growth` y `stress`, un párrafo cada uno.
- `unavailable`: reservado en el tipo por compatibilidad, pero ya no lo devuelve esta ruta (ver
  Feature 19 más abajo): toda generación que falla o no valida cae a contenido pregenerado con
  `personalized` en su lugar.

El prompt nunca lleva género, país, email ni nombre de usuario, ni nada de los clasificadores
(RNF04): sólo `accountType`, `ageRange` y `professionContext`, éste último truncado a 255 caracteres y
tratado como un dato de la persona, no como una instrucción.

## Feature 19: contenido pregenerado

Mismo endpoint y mismo `PersonalizedDescription` de arriba; cambia de dónde salen las cuatro
secciones de `personalized`, según `TEXT_GENERATOR`:

- `TEXT_GENERATOR=pregenerated`: nunca llama a un modelo. `paid_full` con perfil recibe directamente
  el contenido pregenerado de su eneatipo y `accountType` (`individual` si no tiene uno cargado), con
  `status: "personalized"`. No se guarda nada en `results`.
- `TEXT_GENERATOR=bedrock`: si la generación o el parseo fallan, en lugar de `unavailable` la
  respuesta trae el mismo contenido pregenerado, también con `status: "personalized"` — sin guardar
  nada en las columnas `personalized_*`, así que el siguiente pedido vuelve a intentar con Bedrock.

`not_in_plan` y `profile_missing` no cambian: siguen sin llamar a nada, generador o contenido
pregenerado.

## Feature 9: cortes fijos

El test se sirve en tres cortes fijos y anidados de **40, 90 y 145 ítems** (bloques de 40 + 50 + 55).
Después de cada corte la persona ve la precisión estimada del corte que terminó y la del siguiente, y
elige entre ver su resultado o seguir. El corte 1 es el nivel gratuito; el 2 y el 3 requieren tier
pago (una suscripción `active` con `current_period_end` vacío o futuro). Desde la Feature 10 las dos
rutas tienen método en `ApiService`; `HttpApiService` no hace nada además de la llamada.

### `POST /api/attempts/{id}/continue` — `continueTestAttempt(attemptId)`

Sin cuerpo (o `{}`). Sirve el corte siguiente y responde con **el intento en el que sigue el test**:

- **Intento en curso** con su corte entero respondido: se le agregan las filas del corte siguiente,
  con `displayOrder` a continuación (41–90 o 91–145). `200` con el mismo `TestAttempt`; si el corte
  siguiente es pago, el intento pasa a `paid_full`.
- **Intento cerrado:** no se reabre ni se pisa su resultado. Se crea un intento nuevo enlazado al
  anterior, con sus respuestas copiadas (misma pregunta, opción, orden de opciones, `displayOrder` y
  `answeredAt`) y las filas del corte siguiente sin responder. `201` con el `TestAttempt` nuevo, en
  `in_progress` y `paid_full`. Sólo desde el último intento cerrado de la persona, una sola vez, y si
  su versión del cuestionario sigue activa. Si había otro intento en curso, pasa a `abandoned`.

| Status | `code` | `message` |
|---|---|---|
| 402 | `PAID_TIER_REQUIRED` | Para seguir con más preguntas necesitás una suscripción activa. |
| 409 | `CUT_INCOMPLETE` | Quedan preguntas sin responder: respondelas antes de seguir. |
| 409 | `LAST_CUT_REACHED` | Ya respondiste el test completo: no quedan preguntas para seguir. |
| 409 | `ATTEMPT_ALREADY_CONTINUED` | Este test ya se siguió en otro intento. |
| 409 | `ATTEMPT_NOT_CONTINUABLE` | Este intento ya no se puede seguir. Podés empezar un test nuevo. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. (Un cuerpo con campos.) |
| 503 | `QUESTIONNAIRE_UNAVAILABLE` | El cuestionario no está disponible en este momento. Probá de nuevo más tarde. |

Los 409 se evalúan antes que el 402: el pago sólo importa si lo demás permite seguir.
`ATTEMPT_NOT_CONTINUABLE` cubre un intento `abandoned`, un cerrado que no es el último cerrado de la
persona, y uno cuya versión del cuestionario ya no está activa.

### `GET /api/attempts/{id}/cut` — `getCutStatus(attemptId)`

Para la pantalla entre cortes y la de resultado; responde en cualquier estado del intento. `200` con
`CutStatus` (igual a `cut-status.model.ts`):

```json
{
  "currentCut": 1,
  "cutCount": 3,
  "servedItems": 40,
  "answeredItems": 40,
  "nextCutItems": 50,
  "canContinue": false,
  "currentCutAccuracy": 0.62,
  "nextCutAccuracy": 0.71,
  "continuedByAttemptId": null
}
```

- `nextCutItems`: cuántos ítems agrega el corte siguiente; `null` en el último. `nextCutAccuracy`,
  ídem.
- `canContinue`: `true` si `POST .../continue` hoy respondería `200` o `201`. Es la misma regla.
- `currentCutAccuracy` / `nextCutAccuracy`: la precisión estimada de eneatipo de cada corte, entre 0
  y 1 (`estimated_type_accuracy` de `precision_by_items.json`). **Es pública a propósito:** es el
  número que el producto muestra. No sale nada más de los modelos: ni versiones, ni márgenes, ni
  probabilidades.
- `continuedByAttemptId`: si el intento ya se siguió, el id del intento que lo continuó.

## Feature 5: comentarios y contacto

### `POST /api/feedback` — `submitFeedback(input)`

Cuerpo: exactamente `SubmitFeedbackInput`, con los tres campos:

```json
{"testAttemptId": "uuid | null", "rating": 4, "comment": "string | null"}
```

`rating` es un entero de 1 a 5 (ni `4.5`, ni `"4"`, ni `true`). `comment` hasta 2000 caracteres; vacío
o en blanco se guarda como `null`. `testAttemptId` en `null` es un comentario general (desde el
perfil); si viene, el intento tiene que ser del usuario, en cualquier estado. El usuario sale del
token. `204` sin cuerpo: los comentarios no se le vuelven a mostrar a nadie desde la API. Al borrar
la cuenta, `comment` se anula y `rating` queda.

| Status | `code` | `message` |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 404 | `ATTEMPT_NOT_FOUND` | El intento no existe. (Si no existe o es ajeno.) |

### `POST /api/contact-messages` — `submitContactMessage(input)`

**Pública**: no lleva token. Cuerpo: exactamente `SubmitContactMessageInput`:

```json
{"name": "string", "email": "string", "message": "string"}
```

`name` de 1 a 100 caracteres; `email` hasta 254, una dirección ASCII común (`usuario@dominio.tld`);
`message` de 10 a 5000. Se manda un mail con SES a `CONTACT_MAIL_TO`, desde `CONTACT_MAIL_FROM` (por
defecto la misma casilla), con `Reply-To` en el email de quien escribe y el asunto
`Contacto NureonAI: <nombre>`. **No se guarda nada**: ni tabla, ni archivo, ni el contenido en el log.
Los valores que van a cabeceras se reducen a una línea antes: un nombre con saltos de línea no agrega
cabeceras. `204` sin cuerpo.

Límite: `CONTACT_RATE_LIMIT` mensajes (5) por dirección de origen cada
`CONTACT_RATE_WINDOW_SECONDS` (3600). Los cuerpos rechazados por validación no cuentan.

| Status | `code` | `message` |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 429 | `CONTACT_RATE_LIMITED` | Enviaste varios mensajes seguidos. Probá de nuevo más tarde. |
| 503 | `CONTACT_UNAVAILABLE` | No pudimos enviar tu mensaje. Probá de nuevo en unos minutos. |

El 503 es una falla de SES: queda en el log con el código de error y nada del mensaje. No se encola
ni se reintenta: la persona lo vuelve a mandar.

## Feature 6: pagos con Mercado Pago

**Checkout Pro, un pago por un período, sin renovación automática.** Un pago aprobado da el plan
individual por `PLAN_INDIVIDUAL_DAYS` días: una fila de `subscriptions` (`individual`, `active`, con
el período) y una de `payments`. Al vencer, la cuenta vuelve al nivel gratuito. La suscripción
recurrente (preapproval) queda para después del MVP: es una limitación de alcance de la tesis.

**El servidor es la única fuente del nivel.** El navegador nunca manda precio, nivel ni resultado de
un pago: inicia el checkout y, al volver, dice qué pago mirar. El backend lo consulta a Mercado Pago
(`GET /v1/payments/{id}`) y decide. Precio, moneda y días son configuración del backend
(`PLAN_INDIVIDUAL_*`), no código. Ninguna respuesta lleva ids de Mercado Pago.

Documentación de Mercado Pago en la que se apoya cada decisión:
[crear preferencia](https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro-preferences/create-preference/post),
[URLs de retorno](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro-preferences/configure-back-urls),
[obtener pago](https://www.mercadopago.com.ar/developers/es/reference/online-payments/checkout-pro-preferences/get-payment/get),
[estados de pago](https://www.mercadopago.com.ar/developers/es/docs/checkout-api-payments/response-handling/query-results),
[webhooks y firma](https://www.mercadopago.com.ar/developers/es/docs/your-integrations/notifications/webhooks).

| Método de `ApiService` | Ruta | Respuesta | Qué hace `HttpApiService` además de la llamada |
|---|---|---|---|
| `getSubscription` | `GET /api/subscription` | `200` `Subscription` | — |
| `startCheckout` | `POST /api/checkout` | `200` `CheckoutSession` | Sin cuerpo |
| `confirmPayment` | `POST /api/checkout/confirm` | `200` `PaymentConfirmation` | Manda `{paymentId}` |

### `GET /api/subscription` — `getSubscription()`

```json
{"active": false, "currentPeriodEnd": null, "planPrice": 4999.0, "planCurrency": "ARS", "planDays": 30}
```

`active`: la misma regla que el tier (una suscripción `active` con `current_period_end` vacío o
futuro, paga o dada a mano). `currentPeriodEnd`: el fin más lejano entre los períodos activos con fin.
El plan es el de la configuración; los valores del ejemplo son **de ejemplo**.

### `POST /api/checkout` — `startCheckout()`

Sin cuerpo (lo que venga se ignora: el precio no se recibe nunca). Crea una preferencia de Checkout Pro
con un ítem al precio configurado, `external_reference` = el `users.id` (lo único que Mercado Pago
recibe de la persona), `back_urls` success/pending/failure = `PAYMENT_RETURN_URL`, `auto_return:
approved` y vencimiento a los 30 minutos. Responde `{"checkoutUrl": "<init_point>"}` y el frontend
redirige ahí.

| Status | `code` | `message` |
|---|---|---|
| 409 | `ALREADY_SUBSCRIBED` | Ya tenés el plan completo activo. |
| 502 | `PAYMENT_PROVIDER_UNAVAILABLE` | No pudimos comunicarnos con Mercado Pago. Probá de nuevo en unos minutos. |

**Adónde vuelve quien pagó** (`PAYMENT_RETURN_URL`): `FRONTEND_BASE_URL/pago`. Mercado Pago no acepta
`localhost` como retorno, así que con el frontend en localhost (desarrollo con Mercado Pago) se pone
`PUBLIC_API_BASE_URL` (un túnel a este backend) y el retorno pasa por `GET /api/payments/return`, que
redirige al frontend. Con `PAYMENT_PROVIDER=mercadopago` y un retorno en localhost la app no arranca.

### `POST /api/checkout/confirm` — `confirmPayment(paymentId)`

Cuerpo `{"paymentId": "123456789"}` (sólo dígitos, hasta 20). Al volver de Mercado Pago: el backend lee
el pago de Mercado Pago y, si está aprobado y es de esta cuenta, lo registra. Responde:

```json
{"paymentStatus": "approved", "currentPeriodEnd": "2026-11-24T23:39:25+00:00"}
```

`paymentStatus`: `approved`; `pending` (`pending`, `in_process`, `authorized`, `in_mediation`: no se
registra nada todavía; se registra cuando se apruebe, por la notificación o por otra consulta);
`rejected` (`rejected`, `cancelled`, y `refunded` / `charged_back`, que no cambian nada: reembolsos
fuera de alcance). `currentPeriodEnd`, sólo con `approved`.

| Status | `code` | `message` |
|---|---|---|
| 404 | `PAYMENT_NOT_FOUND` | No encontramos ese pago. (Inexistente, o de otra cuenta: misma respuesta.) |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 502 | `PAYMENT_PROVIDER_UNAVAILABLE` | No pudimos comunicarnos con Mercado Pago. Probá de nuevo en unos minutos. |

### La notificación: `POST /api/payments/webhook` (sin sesión)

La configurada en Tus integraciones → Webhooks, evento **Pagos**. La preferencia no lleva
`notification_url`.

1. **Firma** (`app/services/payments/signature.py`): del header `x-signature` (`ts=…,v1=…`) salen `ts`
   y `v1`; el manifest es `id:{data.id en minúsculas};request-id:{x-request-id};ts:{ts};` (sin la parte
   que no llegó); HMAC-SHA256 en hexadecimal con `MERCADOPAGO_WEBHOOK_SECRET`, comparado en tiempo
   constante con `v1`. Si no coincide: `401 INVALID_SIGNATURE`. No se rechaza por antigüedad de `ts`.
2. Si `type` no es `payment`: `200` sin hacer nada.
3. Se lee el pago de Mercado Pago, **nunca se confía en el cuerpo**. Si no existe (404) o no es de esta
   cuenta (403): `200` y se ignora. Si Mercado Pago no responde: `502`, y Mercado Pago reintenta.
4. Mismo registro que `confirm`. **Idempotente:** el UNIQUE de `payments.mercadopago_payment_id`
   garantiza una sola fila, llegue primero la notificación o la persona, y aunque lleguen juntas.
5. Un pago aprobado que no coincide con el plan (moneda o monto: el precio cambió con un checkout
   abierto) no se registra: queda un error en el log con el id del pago, y se resuelve a mano
   (`scripts/grant_subscription.py`).

### `GET /api/payments/return` (sin sesión)

Sólo con `PUBLIC_API_BASE_URL` (ver arriba). `302` a `FRONTEND_BASE_URL/pago?payment_id=…`: reenvía
**sólo** `payment_id`, y sólo si son dígitos. El `status` que agrega Mercado Pago se descarta a
propósito.

### Qué guarda

| Tabla | Qué |
|---|---|
| `subscriptions` | `tier` `individual`, `status` `active`, el período, y en `mercadopago_subscription_id` **el id del pago que lo compró** (Checkout Pro no tiene id de suscripción). NULL sólo en las altas manuales |
| `payments` | `mercadopago_payment_id` (UNIQUE), monto, moneda, `status` `approved`, `paid_at` |

Sin migración: el esquema de la Feature 3 alcanza. Pagos pendientes y rechazados no se guardan.

## Qué queda fuera de las respuestas, a propósito

Toda respuesta sale de un esquema con lista explícita de campos; ningún modelo se serializa entero. Lo
que existe en la base y no sale:

| Dato | Por qué no sale |
|---|---|
| `grouping_system` y `group_label` de preguntas y opciones | Son la clave de corrección del instrumento: con ellas, cualquiera falsea su resultado desde devtools |
| Las predicciones de los clasificadores: grupo, probabilidades, `model_version` | Internas (PDR): no se muestran ni como número ni en palabras |
| `results.confidence_margin` | Ídem. Mostrar la confianza es un punto abierto del plan, no una decisión del backend |
| `questions.version`, `is_active`, `created_at` | Metadatos del banco: el servidor ya resuelve la versión activa |
| `test_attempts.continued_from_attempt_id` | El enlace entre intentos lo expone, al revés, `continuedByAttemptId` de `CutStatus` |
| `users.cognito_sub`, `deleted_at`, `created_at` | Internos de la cuenta |
| `users.consent_accepted_at`, `consent_version` | Constancia del consentimiento (Feature 11): se guarda, no se muestra |
| Los comentarios (`feedback`) | No hay endpoint de lectura: se leen de la base, para el piloto |
| Los mensajes de contacto | No se guardan en ningún lado |
| `subscriptions.mercadopago_subscription_id`, `payments.*` | Ids y registros de Mercado Pago: internos. El estado del plan sale por `GET /api/subscription` |
| `results.personalized_profile_hash`, `personalized_model`, `personalized_at` | Internos: sólo para decidir si hay que regenerar la descripción personalizada (Feature 17) |

`tests/leak_guard.py` revisa toda respuesta JSON de la suite y falla si aparece una clave o un valor de
la clave de corrección o de la salida interna de los clasificadores. `tests/test_contract.py` exige
igualdad exacta de claves: tampoco puede aparecer un campo nuevo sin que se agregue a la interfaz del
frontend.

## Endpoints sin pantalla en el frontend

| Endpoint | Para qué existe |
|---|---|
| `GET /api/health` | Liveness, para el balanceador (Feature 8). No toca la base |
| `GET /api/health/ready` | Readiness: `503 SERVICE_UNAVAILABLE` si no hay base |
| `GET /api/users/me` | El `User` del token. El frontend no lo usa |
| `POST /api/payments/webhook` | La notificación de Mercado Pago (Feature 6). Sin sesión: se prueba con su firma |
| `GET /api/payments/return` | El retorno de Mercado Pago cuando el frontend está en localhost (Feature 6) |

Al revés no hay huecos: todo método de `ApiService` tiene su ruta.
