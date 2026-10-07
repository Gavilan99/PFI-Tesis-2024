# Contrato de la API

Las formas de datos salen de `frontend/nureon/src/app/core/models/` (rama `redesign/frontend`). El JSON
va en camelCase. Todo error tiene la misma forma:

```json
{"error": {"code": "SNAKE_CASE_IN_ENGLISH", "message": "Texto en español."}}
```

## Autenticación

Toda ruta exige `Authorization: Bearer <accessToken>`, salvo `GET /api/health`,
`GET /api/health/ready`, `POST /api/auth/register`, `POST /api/auth/login` y
`POST /api/contact-messages`. Se acepta sólo el access
token del user pool configurado: se verifican la firma, el emisor, el `client_id`, el vencimiento y
`token_use = access`. Un token ausente, vencido, mal firmado o de otro pool responde
`401 UNAUTHORIZED`. La identidad sale del token y de ningún otro lado.

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

Cuerpo: exactamente `RegisterInput`, `{"username", "email", "password"}`. `username` de 3 a 255
caracteres; `password` de 8 a 256. El email se guarda en minúsculas. La cuenta queda confirmada al
crearse: no hay verificación de email.

`201`:

```json
{"user": User, "accessToken": "eyJ...", "expiresIn": 3600}
```

| Status | `code` | `message` |
|---|---|---|
| 409 | `EMAIL_ALREADY_REGISTERED` | Ese email ya está registrado. |
| 400 | `PASSWORD_REJECTED` | La contraseña no cumple los requisitos de seguridad. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 503 | `IDENTITY_UNAVAILABLE` | El servicio de cuentas no está disponible. Probá de nuevo en unos minutos. |

### `POST /api/auth/login` — `login(input)`

Cuerpo: exactamente `LoginInput`, `{"email", "password"}`. El email no distingue mayúsculas.
`200` con la misma forma que el registro.

| Status | `code` | `message` |
|---|---|---|
| 401 | `INVALID_CREDENTIALS` | Email o contraseña incorrectos. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |

Email inexistente y contraseña incorrecta responden igual, a propósito.

### `GET /api/users/me`

`200` con el `User` del token.

### `PATCH /api/users/me` — `updateProfile(userId, input)`

Cuerpo: `UpdateProfileInput`, todos opcionales: `displayName`, `accountType`, `ageRange`, `gender`,
`country`, `professionContext`. Sólo cambian los campos enviados. `null` o `""` borra un campo
opcional; `displayName` no puede quedar vacío. `accountType` se valida contra el enum. El `userId`
que pasa el frontend se ignora (si viene en el cuerpo también). `200` con el `User` actualizado.

| Status | `code` | `message` |
|---|---|---|
| 400 | `EMAIL_NOT_EDITABLE` | El email no se puede modificar. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |

### `DELETE /api/users/me`

Sin pantalla en el frontend (PA-7). Borrado blando con anonimización según la tabla "Borrado de
cuenta" de CLAUDE.md, y borrado del usuario en el proveedor de identidad. `204` sin cuerpo. Después,
el token viejo responde `401` y el mismo email se puede volver a registrar. Si el proveedor falla,
`503 IDENTITY_UNAVAILABLE` y no se anonimiza nada.

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

Sin cuerpo. Si viene uno, sólo puede traer `userId`, que se ignora. El tier lo decide el servidor
(hoy siempre `free_reduced`; la Feature 6 lo resuelve por suscripción). Si el usuario tenía un intento
`in_progress`, pasa a `abandoned` en la misma transacción. Se usa la versión más alta con preguntas
activas, y el subset queda fijado: `SUBSET_SIZE_FREE_REDUCED` (20) o `SUBSET_SIZE_PAID_FULL` (60)
preguntas, la misma cantidad de cada sistema de agrupamiento, mezcladas. `201` con el `TestAttempt`.

| Status | `code` | `message` |
|---|---|---|
| 400 | `TIER_NOT_ACCEPTED` | El tipo de test lo decide el servidor: no se puede elegir al crearlo. |
| 400 | `VALIDATION_ERROR` | Los datos enviados no son válidos. |
| 503 | `QUESTIONNAIRE_UNAVAILABLE` | El cuestionario no está disponible en este momento. Probá de nuevo más tarde. |

El 503 es un problema de carga del banco (no hay versión activa, o algún sistema no alcanza para el
subset), no del usuario: queda en el log como error. No se crea ni se abandona nada.

### `GET /api/attempts/{id}/questions` — `getQuestions(attemptId)`

`200` con **el subset entero**, en el orden del intento. Recargar devuelve lo mismo.

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
a k para las opciones. Las opciones de los ítems `scenario` salen mezcladas por intento (y siempre en
el mismo orden para ese intento); las de los Likert (`multiple_choice`), en el orden del banco, que
es la escala. `grouping_system` y `group_label` no salen nunca.

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

Cierra el intento y calcula su resultado, en la misma transacción (Feature 4.1). `200` con el
`TestAttempt` en `completed`. Llamarlo otra vez devuelve lo mismo y no cambia nada: no vuelve a
clasificar ni pisa el resultado.

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
`descriptionText` es por ahora un texto provisorio fijo por eneatipo.

### `GET /api/attempts/{id}/result` — `getResult(attemptId)`

`200` con el `Result` del intento, si es propio y está `completed`. Cualquier otro caso (no existe,
es ajeno, está `in_progress` o `abandoned`) responde lo mismo:

| Status | `code` | `message` |
|---|---|---|
| 404 | `RESULT_NOT_FOUND` | El resultado no existe. |

Un `{id}` que no es un UUID responde `404 NOT_FOUND`.

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
