# Contrato de la API

Las formas de datos salen de `frontend/nureon/src/app/core/models/` (rama `redesign/frontend`). El JSON
va en camelCase. Todo error tiene la misma forma:

```json
{"error": {"code": "SNAKE_CASE_IN_ENGLISH", "message": "Texto en español."}}
```

## Autenticación

Toda ruta exige `Authorization: Bearer <accessToken>`, salvo `GET /api/health`,
`GET /api/health/ready`, `POST /api/auth/register` y `POST /api/auth/login`. Se acepta sólo el access
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
