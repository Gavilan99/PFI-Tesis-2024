# Estado del backend

## Feature 2: identidad y cuentas

Hecho: registro e ingreso a través del backend, verificación de JWT en toda ruta no pública,
provisioning de `users` atado a `cognito_sub`, perfil (`GET`/`PATCH /api/users/me`) y borrado con
anonimización (`DELETE /api/users/me`). Todo testeado contra el doble local.

### Pendiente

- **Verificación manual contra Cognito real.** El user pool y el app client existen desde el
  2026-10-07 (ver [aws-setup.md](./aws-setup.md)); falta recorrer registro, ingreso y perfil contra
  ellos.
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
