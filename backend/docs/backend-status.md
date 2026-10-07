# Estado del backend

## Feature 3: cuestionario e intentos

Hecho: crear un intento (el anterior en curso pasa a `abandoned`), servir el subset entero en una
request, guardar cada respuesta al elegirla (upsert), reanudar, cerrar (409 si falta alguna) y leer
intentos (`latest`, por id, historial). Contrato en [api-contract.md](./api-contract.md).

- **El subset.** Al crear el intento se eligen, de la versión activa más alta, N preguntas activas, la
  misma cantidad por sistema (`SUBSET_SIZE_FREE_REDUCED`, `SUBSET_SIZE_PAID_FULL`: 20 y 60 por
  defecto, múltiplos de 4). Dentro de cada sistema, al azar, sin controlar la proporción escenario /
  Likert (decidido el 07-10). Queda guardado como filas de `responses` sin opción elegida, con su
  `display_order` y su `option_order`, y no vuelve a sortearse.
- **El tier** sale de `app/services/tiers.py`, que hoy devuelve siempre `free_reduced`. La Feature 6
  cambia esa función y nada más. El cliente no puede mandarlo.
- **La clave de corrección no sale.** Tres capas, con test cada una: las claves (`group_label`,
  `grouping_system`), los valores (ninguna etiqueta del vocabulario canónico) y el orden (opciones de
  escenario mezcladas por intento y guardadas en `responses.option_order`, migración 0003; Likert en
  el orden del banco; preguntas mezcladas). El guardián de las dos primeras revisa **toda** respuesta
  JSON de la suite (`tests/leak_guard.py`), y hay tests que prueban que falla con un serializador que
  filtra a propósito.
- **Enganche de la Feature 4.1:** `_after_completion` en `app/services/attempts.py`. Corre una sola vez
  por intento, dentro de la transacción que lo marca `completed`.
- **`GET /api/attempts/{id}/questions` hace cuatro consultas**, sea el subset de 20 o de 60:
  autenticación, propiedad del intento, ítems, opciones. Ninguna lee `group_label`.

### Limitaciones declaradas

- **El texto de una opción puede delatar su posición en el banco.** El relleno dice "Opción A/B/C",
  y esa letra es el orden del CSV. En el relleno ese orden ya es aleatorio respecto del grupo, así que
  no filtra nada; pero si el banco real numera sus opciones dentro del texto ("a) ...") y las lista
  siempre en el mismo orden de grupos, la mezcla no alcanza. El import tendría que rechazarlo.
- **Una versión servida queda congelada.** Al crear el primer intento sobre la versión 0, el relleno
  ya no se recarga (comportamiento de la Feature 1).
- **Los intentos de `subjects` no tienen endpoints** en este ciclo.

## Feature 2: identidad y cuentas

Hecho: registro e ingreso a través del backend, verificación de JWT en toda ruta no pública,
provisioning de `users` atado a `cognito_sub`, perfil (`GET`/`PATCH /api/users/me`) y borrado con
anonimización (`DELETE /api/users/me`). Todo testeado contra el doble local y verificado a mano contra Cognito real.

### Cognito

- **Verificado contra Cognito real el 2026-10-07** (pool `us-east-2_ZllTXy0w0`, ver
  [aws-setup.md](./aws-setup.md)): registro (cuenta `CONFIRMED`, `sub` igual a `users.cognito_sub`,
  email guardado en minúsculas), ingreso, edición de perfil, email duplicado (409), contraseña
  incorrecta (401), y borrado: fila anonimizada con los demográficos conservados, usuario borrado
  del pool, token viejo en 401 e ingreso rechazado. Ni la contraseña ni el token aparecen en el log.
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
