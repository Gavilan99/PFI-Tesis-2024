# Estado del backend

## Qué está vivo (al cierre de la Feature 7, 2026-10-07)

El frontend real habla con este backend: `HttpApiService` implementa los catorce métodos de
`ApiService` y CU001 a CU004 se recorrieron de punta a punta en el navegador contra el backend local,
con Postgres y Cognito reales. Lo que sigue es qué de eso es real y qué no, sin suavizar.

| Área | Estado real |
|---|---|
| Cuentas (registro, ingreso, perfil, borrado) | **Real.** Cognito en `us-east-2`, verificado de punta a punta desde el navegador |
| Verificación de email | **No existe.** Las cuentas se auto-confirman: cualquiera registra un email ajeno |
| Recuperación de contraseña | **No existe.** Ni pantalla ni método en el contrato |
| Login con Google / Facebook (RNF09) | **No existe.** Los botones del frontend son una ranura inerte |
| Sesión | Access token de 1 hora, sin refresh: al vencer se vuelve a ingresar |
| Banco de preguntas | **Relleno, versión 0.** Lo dice en el texto de cada ítem. El banco v1 no está cargado |
| Clasificación | **`stub` activo por defecto** en desarrollo. **No es ML** (ver abajo) |
| Resultado | Real en el sentido de guardado y servido; el eneatipo sale del `stub` y la descripción es provisoria |
| Comentarios (RF06) | **Real.** Se guardan en la base; no hay pantalla para leerlos |
| Contacto | **Real pero provisorio:** SES en sandbox, casilla de Gmail, sólo a direcciones verificadas |
| Freemium (RF09/RF10) | El tier lo decide el servidor (hoy siempre `free_reduced`), pero **el texto premium viaja en el bundle** |
| Pagos (Mercado Pago, Feature 6) | **0%.** Postergada: no hay endpoint, ni SDK, ni flujo |
| Despliegue (Feature 8) | **0%.** Postergada: no hay dominio, ni ECS, ni RDS, ni S3/CloudFront. Todo corre local |

### Clasificación: qué es cada implementación

`CLASSIFIER_BACKEND` elige una al arrancar; los recorridos de la Feature 7 corrieron con `stub`.

- **`stub`** — conteo de respuestas por grupo, más la tabla canónica (intersección de los cuatro
  sistemas → eneatipo). Determinístico. **No es ML** y no se presenta como tal: cada resultado suyo
  queda marcado `stub-tally-1` en la base. Es el valor por defecto en desarrollo y tests.
- **`legacy_tree`** — el árbol de decisión de 2024, el del documento original, sin reentrenar. **Se
  entrenó sobre un dataset armado por el equipo, no sobre respuestas reales:** son las 81
  combinaciones de un grupo por sistema, 11 copias de cada una, etiquetadas con la tabla canónica.
  **Coincide con la tabla canónica en 77 de 81 combinaciones**; las 4 diferencias son errores del
  árbol sobre sus propios datos. Recibe un solo grupo por sistema, así que hereda los desempates del
  conteo. Es el candidato para la demo, pero no aprende nada que la tabla no diga.
- **`trained`** — los cuatro Random Forest del diseño nuevo. **No existe todavía:** sin artefactos,
  la app no arranca con este valor, y nunca cae al stub.

En `production` la variable es obligatoria, sin valor por defecto: elegir qué se muestra en la defensa
es una decisión explícita.

### Lo que sabe el navegador

- **La clave de corrección no sale.** Ni `group_label`, ni `grouping_system`, ni probabilidades,
  margen o versión de modelo: lo vigila `tests/leak_guard.py` sobre toda respuesta de la suite, y
  `tests/test_contract.py` exige que las claves de cada respuesta sean exactamente las de su interfaz
  TypeScript. Verificado también a mano en las respuestas reales de preguntas y resultado.
- **El texto premium sí está en el navegador.** El contenido "En crecimiento y bajo estrés" de los
  nueve eneatipos viaja en el bundle del frontend (`eneatype-content.ts`), y en `/resultados` además
  se renderiza en el DOM y se difumina con CSS cuando el intento es `free_reduced`. El tier lo decide
  el servidor, pero quien abra devtools lee el texto.
  Mover ese contenido al backend y servirlo según el tier es trabajo de la Feature 6.

### Contacto

Sale por SES en **modo sandbox**, desde y hacia una **casilla provisoria de Gmail** (va sólo en el
`.env`): en el sandbox SES sólo entrega a direcciones verificadas, que hoy es esa casilla y nada más.
Los mails probablemente caigan en spam hasta tener dominio propio con DKIM (PA-21). El **límite de
envíos cuenta por proceso**, en memoria: con varios workers cada uno permite el límite, y reiniciar lo
pone en cero. En la Feature 7 los recorridos usaron `MAIL_SENDER=local`, que no manda nada; SES real
se probó en la Feature 5.

### Integración (Feature 7)

- **`HttpApiService`** implementa los catorce métodos contra `environment.apiBaseUrl`. El formato de
  error del backend llega a los formularios como un `Error` con el `message` en español; donde el
  contrato admite `null` (`getLatestAttempt` sin intentos, `getAttempt` con 404) se devuelve `null`.
- **Token** en `localStorage`, enviado por un interceptor sólo al backend. Se borra al cerrar sesión
  y ante un 401 (que además cierra la sesión). Probado: después de cerrar sesión `localStorage` queda
  vacío; con una cuenta borrada, el primer pedido devuelve 401 y la app vuelve a `/ingresar`.
- **Recargar a mitad del test** retoma en el mismo ítem leyendo la base (`latest`, `questions`,
  `responses`); en `localStorage` no queda estado del mock.
- **Otra cuenta no ve nada de la anterior:** historial vacío, y el intento ajeno responde 404 en
  intento, respuestas y resultado.
- **El build `demo` sigue usando el mock**, sin interceptor: es el respaldo de la defensa.
- **El build de producción apunta a `https://api.nureon.ai`, que no existe** hasta la Feature 8.

### Limitaciones declaradas

- **Al cerrar sesión, la pantalla actual no se va.** `AppComponent.onLogoutRequested` sólo vacía el
  usuario: si se cierra sesión en `/perfil`, los datos de esa cuenta siguen en pantalla hasta navegar.
  No hay pedidos ni token detrás. Es un cambio de componente, fuera del alcance de esta feature.
- **Los formularios no conocen los máximos del backend** (100 / 254 / 5000 en contacto, 2000 en el
  comentario). Pasarse muestra el error genérico del formulario, legible, y el formulario sigue
  usable. Agregar los máximos en pantalla es una tarea aparte.
- **Un token vencido con el test abierto** hace fallar el próximo pedido con el error del test; la
  sesión se cierra y hay que volver a ingresar. Sin refresh token no hay renovación silenciosa.

## Feature 5: comentarios y contacto

Hecho: `POST /api/feedback` guarda el comentario (RF06) y `POST /api/contact-messages` manda el
formulario de contacto por mail, sin guardarlo. Contrato en [api-contract.md](./api-contract.md).

- **Comentarios.** El usuario sale del token; un intento ajeno es el mismo 404 que uno inexistente.
  Rating entero estricto de 1 a 5 (además del CHECK de la tabla); comentario hasta 2000 caracteres.
  No hay endpoint de lectura: alimentan la prueba piloto y se leen de la base.
- **Borrado de cuenta**, de punta a punta: un usuario comenta por la API, borra su cuenta, y sus
  comentarios quedan con `comment` en NULL y el `rating` intacto. Los de otros, sin tocar.
- **Contacto, detrás de una costura** (`app/services/mail/`), igual que la identidad: `SesMailSender`
  (SES v2, `SendEmail` con el MIME armado por el backend) y `LocalMailSender`, un doble en memoria
  para tests y desarrollo. `MAIL_SENDER` elige; `test` fuerza `local` y `production` rechaza `local`.
- **Nada del mensaje se guarda ni se loguea.** Un test vuelca todas las filas de todas las tablas y
  todo lo que se loguea, a nivel DEBUG y en todos los loggers, y busca un marcador del mensaje.
- **Inyección de cabeceras.** Nombre y email se reducen a una línea (todo carácter de control pasa a
  espacio) antes de ir a `Reply-To` y `Subject`; además el email sólo acepta una dirección ASCII
  común. El sobre de SES sale de la configuración, no del cuerpo.
- **Límite por origen:** ventana deslizante en memoria (`app/services/rate_limit.py`), 5 por hora
  por dirección por defecto.
- **La cadena del historial** (Features 3 y 4.1) tiene su test de punta a punta: dos intentos
  cerrados y uno en curso, el historial del más nuevo al más viejo, resultado para los cerrados y
  404 para el abierto.

### SES

**Configurado el 2026-10-07**, por consola (el usuario `nureon-dev` no tiene permisos de SES ni de
IAM): identidad de la casilla verificada en `us-east-2` y política en línea con `ses:SendEmail` y
`ses:SendRawEmail` (el contenido raw se autoriza como `SendRawEmail`). Procedimiento en
[aws-setup.md](./aws-setup.md#3-ses). La casilla va sólo en el `.env` local. Prueba manual con `curl`
contra SES real: `204`, sin errores en el log.

### Limitaciones declaradas

- **El límite de envíos vive en la memoria de cada proceso.** Con varios workers de gunicorn cada
  uno permite el límite; reiniciar lo pone en cero.
- **Detrás del ALB (Feature 8) el origen es el balanceador**, no quien escribe: sin `ProxyFix`
  configurado para un salto, todos comparten un solo contador. Va con el despliegue.
- **Emails con caracteres no ASCII se rechazan** en el formulario de contacto. Es el precio de
  aceptar sólo lo que puede ir a una cabecera sin codificar.
- **Remitente de Gmail:** los mensajes probablemente caigan en spam hasta tener dominio propio (PA-21).
- **El frontend no conoce los máximos** (100 / 254 / 5000 en contacto, 2000 en el comentario): un
  texto más largo recibe el error genérico de envío. Agregar `maxlength` a los formularios es una
  tarea aparte del frontend (decidido en la Feature 7, que no toca componentes).

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
