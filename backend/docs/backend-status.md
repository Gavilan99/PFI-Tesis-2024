# Estado del backend

## Feature 4.1: resultado y ranura de inferencia

Hecho: cerrar un intento lo clasifica y guarda, en la misma transacción, las cuatro filas de
`classifier_predictions` y la de `results`; `GET /api/attempts/{id}/result` devuelve el `Result`.
Contrato en [api-contract.md](./api-contract.md). Detalle de la costura, los backends y las
mediciones en [app/ml/README.md](../app/ml/README.md).

- **El scaffold de la 4.0 vive en `app/ml/`** (movido con `git mv` desde `backend/models/`). Sus
  sistemas usan el vocabulario canónico: `TAXONOMIES` sale de `app/db/models/enums.py`. La tabla
  canónica no cambió. `python -m app.ml.pipeline` sigue corriendo sobre datos sintéticos.
- **La costura** es `app/ml/classification.py`: entran las respuestas con su grupo resuelto en el
  servidor, salen los cuatro sistemas (grupo y distribución), el eneatipo, el margen y la versión de
  modelo. `CLASSIFIER_BACKEND` elige la implementación al arrancar (`app/ml/registry.py`); la ruta
  de cierre recibe la que esté, sin saber cuál es. Un test registra una implementación falsa y entra
  por configuración sin tocar rutas ni servicios.
- **`stub`** (`stub-tally-1`): conteo por `group_label`. No es ML. Escenario suma 1; Likert suma
  `(posición − 1) / 4` a su grupo objetivo (opción 1 suma 0, opción 5 suma 1). Fracciones exactas.
  Empates: dentro de un sistema, el primer grupo del vocabulario; entre eneatipos, el número más bajo.
- **`legacy_tree`** (`legacy-tree-1`): el árbol de 2024, **sin reentrenar**: el `.pkl` original se
  guardó con scikit-learn 1.5.2, la versión fijada, y carga sin advertencias. Copia byte a byte en
  `app/ml/legacy/`, con el dataset y un script de entrenamiento con rutas relativas que reproduce
  0,94 / 0,94 y un árbol idéntico. El eneatipo lo decide el árbol; las filas de
  `classifier_predictions` son las del conteo.
- **`trained`** no arranca: sin los cuatro artefactos lo dice y se detiene; con artefactos también,
  hasta que esté definida la codificación respuestas → features. Nunca cae al stub.
- **En `production`, `CLASSIFIER_BACKEND` es obligatoria**, sin valor por defecto.
- **Lo interno no sale.** El guardián de la Feature 3 ahora también rechaza `probabilities`,
  `predicted_group`, `confidence_margin` y `model_version` en cualquier forma, toda clave que
  contenga `confidence`, `margin` o `probabilit`, y todo texto que nombre una versión de modelo.
- **`description_text`** es provisorio: el resumen de una frase de cada eneatipo, copiado tal cual
  del frontend a `app/services/result_descriptions.py`. La redacción final es otra tarea.
- **Cerrar dos veces** no reclasifica ni pisa. **Si la clasificación falla**, el intento sigue
  `in_progress` sin filas, y responde `500 RESULT_NOT_GENERATED`.

### Mediciones

- `legacy_tree` contra la tabla canónica, en las 81 combinaciones de un grupo por sistema:
  **coinciden en 77** (y en las 9 que son filas exactas de la tabla). El dataset de 2024 coincide con
  la tabla en sus 891 filas: las 4 diferencias son errores del árbol sobre sus propios datos.
- 1000 intentos al azar sobre el relleno (subset de 20, opción uniforme): `stub` reparte entre 100 y
  123 por eneatipo; `legacy_tree`, entre 53 (tipo 4) y 158 (tipo 1). En el 58,5% de esos intentos
  algún sistema queda empatado; para `legacy_tree` eso decide la entrada del árbol, para `stub` no.

### Limitaciones declaradas

- **El stub no es un modelo** y no se presenta como uno. Todo resultado suyo queda identificado por
  `stub-tally-1` en `classifier_predictions.model_version`.
- **El peso del Likert** (`(posición − 1) / 4`) es una regla del stub, no una calibración.
- **`legacy_tree` recibe un solo grupo por sistema**; con empates, el primero del vocabulario. Con
  respuestas al azar ese desempate sesga su entrada.

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
