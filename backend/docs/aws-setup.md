# AWS: lo que existe y cómo se recrea

Región **`us-east-2`** (la única que permite la cuenta). Todo comando lleva
`--profile nureon --region us-east-2` explícitos; el perfil `default` no se usa nunca.

Sólo se crea lo de esta lista. Ids no secretos; ninguna credencial va en este archivo.

| Recurso | Id | Costo mensual |
|---|---|---|
| User pool `nureon-dev` | `us-east-2_ZllTXy0w0` | US$0 (plan Lite, 10.000 usuarios activos gratis por mes) |
| App client `nureon-backend` | `216kporbavdvjbtthon6p28vel` | US$0 |
| Identidad de SES (casilla de contacto, sólo en `.env`) + política `nureon-backend-ses-send` | ver sección 3 | US$0 al volumen del piloto |

## 1. User pool

Creado el 2026-10-07. Ingreso por email (sin distinguir mayúsculas), sin MFA, contraseña de mínimo
8 sin exigir tipos de caracter (igual al formulario de registro), auto-registro cerrado (sólo el
backend crea cuentas), sin recuperación por email ni atributos auto-verificados: el pool no manda
mensajes.

```powershell
aws cognito-idp create-user-pool `
  --pool-name nureon-dev `
  --user-pool-tier LITE `
  --username-attributes email `
  --username-configuration CaseSensitive=false `
  --mfa-configuration OFF `
  --policies "PasswordPolicy={MinimumLength=8,RequireUppercase=false,RequireLowercase=false,RequireNumbers=false,RequireSymbols=false,TemporaryPasswordValidityDays=1}" `
  --admin-create-user-config AllowAdminCreateUserOnly=true `
  --account-recovery-setting "RecoveryMechanisms=[{Priority=1,Name=admin_only}]" `
  --deletion-protection INACTIVE `
  --user-pool-tags Project=nureon,Environment=dev `
  --profile nureon --region us-east-2
```

## 2. App client del backend

Creado el 2026-10-07. Sin secreto. Un único flujo, `ALLOW_ADMIN_USER_PASSWORD_AUTH`: el del lado del
servidor (`AdminInitiateAuth`), que se autoriza con IAM. SRP y `USER_PASSWORD_AUTH` quedan
deshabilitados, así que nadie ingresa contra Cognito sin pasar por el backend. Un email inexistente
responde igual que una contraseña incorrecta. El backend usa sólo el access token (60 minutos); el
ID y el refresh token quedan en el mínimo que permite Cognito y no se devuelven.

```powershell
aws cognito-idp create-user-pool-client `
  --user-pool-id us-east-2_ZllTXy0w0 `
  --client-name nureon-backend `
  --no-generate-secret `
  --explicit-auth-flows ALLOW_ADMIN_USER_PASSWORD_AUTH `
  --prevent-user-existence-errors ENABLED `
  --enable-token-revocation `
  --access-token-validity 60 `
  --id-token-validity 60 `
  --refresh-token-validity 60 `
  --token-validity-units AccessToken=minutes,IdToken=minutes,RefreshToken=minutes `
  --profile nureon --region us-east-2
```

## 3. SES

Creados por consola el 2026-10-07. Los dos pasos que crean algo en AWS se hacen **por consola**, en
**`us-east-2`**: el usuario `nureon-dev` (perfil `nureon`) sólo tiene `AmazonCognitoPowerUser`, así
que no puede crear identidades de SES ni darse permisos a sí mismo, y el perfil `default` no se usa
nunca. En los ejemplos, `contacto@example.com` está en lugar de la casilla real, que va sólo en el
`.env` local.

Qué hace falta, según la documentación vigente de SES (consultada el 2026-10-07):

- La cuenta arranca en el **sandbox**, por región: sólo manda **a** direcciones verificadas, hasta 200
  mails por día y 1 por segundo. Alcanza: el destino es nuestra casilla.
- Hay que verificar el **remitente** (`From`) y, en el sandbox, también el **destinatario**. El
  backend manda desde la misma casilla que recibe (`CONTACT_MAIL_FROM` vacío), así que se verifica
  **una sola identidad de tipo email**.
- `Reply-To` no se verifica: es el email de quien escribe, y es lo que hace que responder le llegue.
- Permiso de IAM: **`ses:SendEmail` y `ses:SendRawEmail`** sobre el ARN de la identidad. El backend
  llama a `SendEmail` (API v2) con el MIME ya armado (contenido raw), y SES lo autoriza como
  `ses:SendRawEmail`: con `ses:SendEmail` solo responde `AccessDeniedException` (comprobado el
  2026-10-07).
- Costo: US$0,10 cada 1.000 mails. Con el límite de 5 por hora por origen y el uso del piloto, US$0.

> **Spam.** Con una casilla de Gmail como remitente es probable que los mensajes caigan en spam: SES
> manda en nombre de `gmail.com` sin poder firmar por ese dominio, y la política DMARC de Gmail lo
> penaliza. La solución de fondo es un dominio propio verificado en SES (DKIM), que está postergado
> (PA-21). Mientras tanto, revisar la carpeta de spam y marcar el primer mensaje como "no es spam".

### a. Identidad de la casilla

1. Consola de AWS, región **us-east-2 (Ohio)** → **Amazon SES** → **Identities** →
   **Create identity**.
2. **Identity type: Email address**, la casilla (`contacto@example.com`). Sin configuration set ni
   tags obligatorios. **Create identity**.
3. SES manda a esa casilla un mail de verificación: abrir el link (vence a las 24 horas; si venció,
   **Send verification email** desde la identidad). La identidad tiene que quedar en **Verified**.

### b. Permiso para el usuario de desarrollo

1. Consola → **IAM** → **Users** → `nureon-dev` → **Permissions** → **Add permissions** →
   **Create inline policy** → editor **JSON**.
2. Pegar la política de abajo con la casilla real, nombrarla `nureon-backend-ses-send` y crearla.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NureonBackendContactMail",
      "Effect": "Allow",
      "Action": ["ses:SendEmail", "ses:SendRawEmail"],
      "Resource": "arn:aws:ses:us-east-2:517207997735:identity/contacto@example.com"
    }
  ]
}
```

Es sólo enviar, sólo con esa identidad, sólo en `us-east-2`. Es también lo que lleva el rol del
backend en la Feature 8.

### Cómo se deshace

- **El permiso:** IAM → Users → `nureon-dev` → Permissions → seleccionar
  `nureon-backend-ses-send` → **Remove**. El backend pasa a responder `503 CONTACT_UNAVAILABLE`.
- **La identidad:** SES (us-east-2) → Identities → seleccionar la casilla → **Delete**. Volver a
  crearla pide verificarla de nuevo.

## Configuración del backend

En `backend/.env` (no se commitea):

```
IDENTITY_PROVIDER=cognito
AWS_PROFILE=nureon
COGNITO_REGION=us-east-2
COGNITO_USER_POOL_ID=us-east-2_ZllTXy0w0
COGNITO_APP_CLIENT_ID=216kporbavdvjbtthon6p28vel
MAIL_SENDER=ses
SES_REGION=us-east-2
CONTACT_MAIL_TO=contacto@example.com
```

## Permisos de IAM del backend

En desarrollo el backend corre con el perfil `nureon` (usuario de IAM `nureon-dev`), que ya tiene
permisos de Cognito más amplios que estos: no se creó ninguna política nueva. Cuando el backend
corra con su propio rol (Feature 8, despliegue), ese rol lleva sólo esto:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NureonBackendCognito",
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminCreateUser",
        "cognito-idp:AdminSetUserPassword",
        "cognito-idp:AdminInitiateAuth",
        "cognito-idp:AdminGetUser",
        "cognito-idp:AdminDeleteUser"
      ],
      "Resource": "arn:aws:cognito-idp:us-east-2:517207997735:userpool/us-east-2_ZllTXy0w0"
    }
  ]
}
```

Verificar el access token no necesita IAM: el JWKS del pool es público
(`https://cognito-idp.us-east-2.amazonaws.com/us-east-2_ZllTXy0w0/.well-known/jwks.json`).

## Cómo se borra

La identidad de SES y su permiso se borran por consola: ver [3. SES](#cómo-se-deshace).

El user pool:

Borrar el pool borra sus usuarios y sus app clients. No tiene protección contra borrado.

```powershell
aws cognito-idp delete-user-pool --user-pool-id us-east-2_ZllTXy0w0 --profile nureon --region us-east-2
```
