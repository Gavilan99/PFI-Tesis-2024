# AWS: lo que existe y cómo se recrea

Región **`us-east-2`** (la única que permite la cuenta). Todo comando lleva
`--profile nureon --region us-east-2` explícitos; el perfil `default` no se usa nunca.

Sólo se crea lo de esta lista. Ids no secretos; ninguna credencial va en este archivo.

| Recurso | Id | Costo mensual |
|---|---|---|
| User pool `nureon-dev` | `us-east-2_ZllTXy0w0` | US$0 (plan Lite, 10.000 usuarios activos gratis por mes) |
| App client `nureon-backend` | `216kporbavdvjbtthon6p28vel` | US$0 |

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

## Configuración del backend

En `backend/.env` (no se commitea):

```
IDENTITY_PROVIDER=cognito
AWS_PROFILE=nureon
COGNITO_REGION=us-east-2
COGNITO_USER_POOL_ID=us-east-2_ZllTXy0w0
COGNITO_APP_CLIENT_ID=216kporbavdvjbtthon6p28vel
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

Borrar el pool borra sus usuarios y sus app clients. No tiene protección contra borrado.

```powershell
aws cognito-idp delete-user-pool --user-pool-id us-east-2_ZllTXy0w0 --profile nureon --region us-east-2
```
