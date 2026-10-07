# Estado del backend

## Feature 2: identidad y cuentas

Hecho: registro e ingreso a través del backend, verificación de JWT en toda ruta no pública,
provisioning de `users` atado a `cognito_sub`, perfil (`GET`/`PATCH /api/users/me`) y borrado con
anonimización (`DELETE /api/users/me`). Todo testeado contra el doble local.

### Pendiente

- **El user pool de Cognito no existe todavía.** La implementación real (`CognitoIdentityProvider`)
  está escrita y testeada contra un cliente boto3 con stubs, pero no se probó contra un pool de
  verdad. Al crearlo: ingreso por email, sin MFA, app client sin secreto con sólo
  `ALLOW_ADMIN_USER_PASSWORD_AUTH`, y política de contraseña de mínimo 8 sin exigir tipos de
  caracter (lo que pide el formulario de registro). El backend necesita
  `cognito-idp:AdminCreateUser`, `AdminSetUserPassword`, `AdminInitiateAuth`, `AdminGetUser` y
  `AdminDeleteUser` sobre ese pool.
- **Credenciales de AWS.** Todo comando lleva `--profile nureon` (el usuario de IAM `nureon-dev`).
  El backend recibe el perfil por `AWS_PROFILE` y se lo pasa a boto3 de forma explícita; `default`
  se rechaza al arrancar, porque en las máquinas de desarrollo tiene acceso completo a la cuenta.

### Limitaciones declaradas

- **El email no se verifica.** Con auto-confirmación, cualquiera registra un email ajeno
  (decisión 1 del plan del 05-10). No hay recuperación de contraseña: no hay pantalla ni método en
  el contrato.
- **Sin refresh token.** El login devuelve sólo el access token; al vencer, se vuelve a ingresar.
- **Los demográficos se conservan al borrar una cuenta.** Con una muestra chica como la del piloto
  son cuasi-identificadores (decisión 8). Va declarado en el documento.
- **`subjects.linked_user_id` no se toca al borrar.** La columna está reservada y sin uso.
- **El doble local guarda las cuentas en memoria.** Reiniciar el proceso de desarrollo las borra;
  las filas de `users` quedan y ese email ya no se puede registrar de nuevo hasta limpiar la base.
