# Despliegue: runbook

Cómo se crea, se actualiza, se vuelve atrás y se apaga NureonAI en AWS. Los scripts viven en
[`backend/infra/`](../infra/): uno por paso, en PowerShell 5.1, re-ejecutables (lo que ya existe se
deja como está) y con sus variables arriba. Los nombres compartidos están en
[`_common.ps1`](../infra/_common.ps1).

> **Estado (2026-10-18): nada creado en AWS.** Los scripts están escritos y probados en lo que se
> puede probar sin crear recursos: `00-check`, `status`, el build de la imagen y el del frontend desde
> un ref (`-BuildOnly`), y el humo contra el backend local. El despliegue se corre en diciembre, para
> la demo: ver [Costo y créditos](#costo-y-créditos).

## Arquitectura

| Pieza | Dónde | Notas |
|---|---|---|
| Frontend | S3 privado + CloudFront con OAC | Dominio `*.cloudfront.net`; sólo esa distribución lee el bucket |
| API | ECS Express Mode (Fargate) | Dominio `*.ecs.us-east-2.on.aws`, HTTPS con certificado y ALB que crea Express Mode. El frontend la llama con CORS; no pasa por CloudFront |
| Base | RDS PostgreSQL 16, subnets privadas | Sin acceso público, cifrada, backups 7 días, contraseña maestra administrada por Secrets Manager |
| Imagen | ECR `nureon-api` | Tags inmutables: el tag dice de qué ref (y de qué modelos) salió |
| Secretos | Secrets Manager | El de RDS (`rds!db-…`) y `nureon/prod/app` (`SECRET_KEY`) |
| Logs | CloudWatch Logs `/aws/ecs/nureon/nureon-api` | 30 días |
| Identidad, mail | Cognito `us-east-2_ZllTXy0w0`, SES | Ya existían ([aws-setup.md](./aws-setup.md)); se reusan |

Todo en `us-east-2`, y los datos no salen de AWS (Ley 25.326): la base no tiene IP pública ni ruta a
internet, las tareas hablan con Cognito, SES y Secrets Manager por sus endpoints regionales con TLS
(sin endpoints de VPC: no hacen falta y cuestan por hora), y los logs no llevan cuerpos ni
identificadores personales.

Red: las tareas corren en dos subnets públicas por defecto (2a, 2b) con IP pública, sin NAT Gateway.
Express Mode crea dos security groups: el del ALB (443 desde internet) y el del servicio (el puerto
del contenedor sólo desde el ALB). La base acepta 5432 sólo desde el del servicio.

## Requisitos de la máquina

- Perfil `nureon-deploy` del AWS CLI (usuario de IAM con
  [`iam/nureon-deployer-policy.json`](../infra/iam/nureon-deployer-policy.json); ver
  [aws-setup.md](./aws-setup.md#4-perfil-de-despliegue)). Nunca `default`.
- AWS CLI 2.37 o mayor (trae Express Mode), Docker Desktop, git, Node 20+ con npm.
- `backend/.env` con `CONTACT_MAIL_TO`: la casilla de contacto va a la configuración del servicio y al
  permiso de SES desde ahí, nunca al repositorio.

Se corren desde la raíz del repo: `powershell -File backend\infra\<script>.ps1`.

## Primer despliegue

En orden. Antes de cada paso que crea algo, mirar su costo (está en la cabecera de cada script).

| Paso | Script | Qué hace | Tiempo |
|---|---|---|---|
| 0 | `00-check.ps1` | Sólo lectura: perfil, plan y créditos, cada servicio, Express Mode, `--dry-run` de la red | 1 min |
| 1 | `01-network.ps1` | Subnets privadas (2a, 2b), tabla de rutas sin internet gateway, DB subnet group, security group de la base sin reglas | 1 min |
| 2 | `02-database.ps1` | RDS; deja la rotación del secreto maestro en 365 días | ~10 min |
| 3 | `03-app-secret.ps1` | `SECRET_KEY` generada local, sólo en Secrets Manager | seg. |
| 4 | `04-registry.ps1` | Repositorio ECR, inmutable, con escaneo y las últimas 10 imágenes | seg. |
| 5 | `05-roles.ps1` | Roles de ejecución, de tarea y de infraestructura | seg. |
| 6 | `06-cluster.ps1` | Cluster `nureon` y log group | seg. |
| 7 | `07-frontend-infra.ps1` | Bucket, OAC, distribución. Imprime el dominio del frontend | ~5 min |
| 8 | `08-image.ps1 -Ref <tag o commit> -Models <carpeta>` | Build desde `git archive`, con los artefactos **reales** de los modelos, y push. Imprime el tag de la imagen | ~5 min |
| 9 | `09-service.ps1 -ImageTag <tag> -Classifier trained` | Crea el servicio; abre 5432 en la base al security group del servicio. Imprime la URL de la API | ~10 min |
| 10 | `10-task.ps1 -Job migrate` | `alembic upgrade head` | 2 min |
| 10 | `10-task.ps1 -Job bank-dry-run` | El banco v4.1.2 de la imagen, simulado: tiene que decir 145 preguntas, 533 opciones | 2 min |
| 10 | `10-task.ps1 -Job bank-load` | El mismo, como versión 1 activa | 2 min |
| 11 | `11-frontend-deploy.ps1 -Ref <tag o commit>` | Build del frontend con `apiBaseUrl` = URL de la API, subida e invalidación | ~5 min |
| 12 | `12-smoke.ps1` | Humo de punta a punta. **Anotar el id de la cuenta abajo** | 1 min |

**La imagen siempre lleva los artefactos reales** (desde la Feature 9): el plan de cortes 40/90/145
sale de su `manifest.json`, y sin él la app no arranca, tampoco con el stub. Con artefactos sintéticos
(`scripts/make_dev_artifacts.py`) la app se niega a arrancar en producción.

**El banco se carga antes de que nadie cree un intento**, ni siquiera el humo: una sola respuesta
congela la versión. Todos los códigos del manifest (`Q001`…`Q145`) tienen que existir como preguntas
activas de la versión cargada; si falta alguno, crear un intento responde 503. **En producción nunca se corre `seed_filler_bank.py`**: no hay tarea para eso y el
script ni siquiera está en la imagen.

En la primera vuelta (Feature 8) la imagen sale de la rama `feature/be-08-deploy`. Después del release
`v1.0.0` se vuelve a desplegar desde el tag, con los pasos de la sección siguiente.

**En un entorno nuevo (base vacía) el orden es siempre este**, también para versiones posteriores:
servicio (paso 9) y después `migrate` sin `-ImageTag`. El orden de la sección siguiente es para
actualizar un entorno que ya tiene servicio y base.

## Desplegar una versión nueva

A producción va sólo lo que está en `main`, desde un tag `vX.Y.Z`.

```powershell
powershell -File backend\infra\08-image.ps1 -Ref v1.0.1 -Models C:\ruta\a\artifacts   # tag: v1.0.1-models-<hash>
powershell -File backend\infra\10-task.ps1 -Job migrate -ImageTag v1.0.1-models-<hash>   # sólo si trae migraciones
powershell -File backend\infra\09-service.ps1 -ImageTag v1.0.1-models-<hash> -Classifier trained   # canario
powershell -File backend\infra\11-frontend-deploy.ps1 -Ref v1.0.1
powershell -File backend\infra\logs.ps1 -Minutes 15 -Scan
```

**Las migraciones van antes del servicio**, con la imagen nueva: `-ImageTag` corre las migraciones de
esa imagen en una task definition de un solo uso (familia `nureon-api-oneoff`, que se desregistra al
terminar), sin tocar el servicio, que sigue con el código viejo. Así las columnas ya existen cuando
el código nuevo empieza a usarlas, y no hay ninguna ventana con el registro o el ingreso caídos.

Eso exige que **toda migración sea compatible con el código que está corriendo**: agregar tablas o
columnas nullables (o con valor por defecto en la base), nunca borrar ni renombrar en la misma versión.
El código viejo no lee lo que no conoce. Un cambio que rompe se parte en dos versiones: primero la que
deja de usar la columna, después la que la borra.

La tarea corre con la imagen nueva pero con la configuración del servicio, que es la del código viejo.
Por eso las migraciones leen sólo la URL de la base (`migrations/env.py`, `database_url`) y no la
configuración completa: una variable que el código nuevo exige y el servicio todavía no tiene (como
`CONSENT_VERSION` en la Feature 11) no las frena. Lo cubre `test_production_migrations_need_only_the_database`.

Qué corre siempre se sabe: el tag de la imagen es el tag de git (o `sha-<commit>`), y la imagen lleva
`org.opencontainers.image.revision` (el commit), `nureon.ref` y `nureon.models`.

### Con los modelos entrenados

Los artefactos no están versionados: los escribe `app/ml/training/train.py` en otra máquina, sobre los
datos privados del piloto (`cut_040/`, `cut_090/`, `cut_145/`, `manifest.json`,
`precision_by_items.json`). **La imagen se construye con esos artefactos reales y el servicio corre con
`CLASSIFIER_BACKEND=trained`:**

```powershell
powershell -File backend\infra\08-image.ps1 -Ref v1.1.0 -Models C:\ruta\a\artifacts   # tag: v1.1.0-models-<hash>
powershell -File backend\infra\09-service.ps1 -ImageTag v1.1.0-models-<hash> -Classifier trained
```

- **La app no arranca con artefactos sintéticos en producción** (`model_version` que empieza con
  `synthetic-`, los de `scripts/make_dev_artifacts.py`), con ningún clasificador.
- Tampoco arranca si el manifest no tiene los cortes 40/90/145 anidados, si falta alguno de los doce
  `.joblib`, o si scikit-learn o numpy de la imagen no son las versiones con que se entrenó (el
  manifest las guarda; `requirements.txt` fija scikit-learn).
- Antes, probarlo local con el compose de producción (`CLASSIFIER_BACKEND: trained` y los artefactos
  reales en `backend/app/ml/artifacts/`).
- Si arranca mal en AWS, el ALB no lo da por sano, el despliegue canario no pasa el tráfico y la
  versión anterior sigue sirviendo. Para volver al stub con la misma imagen (el stub sirve por el mismo
  plan de cortes): `09-service.ps1 -ImageTag <el mismo> -Classifier stub`.

## Migraciones, carga del banco y altas manuales

Son tareas sueltas (`run-task`) con la imagen y la task definition del servicio, en sus subnets y con
su security group; nunca corren al arrancar la app. La excepción es `-Job migrate -ImageTag <tag>`,
que usa la task definition del servicio con otra imagen (ver "Desplegar una versión nueva"). `10-task.ps1` espera a que la tarea termine,
imprime su log y falla si salió con un código distinto de 0.

- `-Job migrate`: `alembic upgrade head`. Con `-ImageTag <tag>`, las migraciones de esa imagen, antes
  de desplegarla. Sin `-ImageTag`, las de la imagen que corre el servicio (en un entorno nuevo).
- `-Job bank-dry-run` / `-Job bank-load`: `import_question_bank.py` con el CSV de la imagen
  (`bank/NureonAI Prototype v4.1.2.csv`). Una versión con respuestas no se modifica más: un banco
  cambiado entra como versión nueva, con `-BankVersion 2`, otra imagen que traiga ese CSV, y
  `--activate` desactiva las demás.
- `-Job grant-subscription -Email <email> -Days <N>`: `scripts/grant_subscription.py`. **Alta manual de
  una suscripción, sin pago asociado**, para las cuentas de las pruebas de usuario mientras no exista
  la Feature 6 (Mercado Pago): da el tier pago (cortes 2 y 3) durante N días (1 a 366). Escribe una fila
  de `subscriptions` `individual`, `active`, con `mercadopago_subscription_id` en NULL y sin fila en
  `payments`. La cuenta tiene que existir (registrada desde el frontend). El log nombra la cuenta por
  su `users.id`, nunca por el email; el email sí queda en el override de la tarea (ECS, CloudTrail).

  ```powershell
  powershell -File backend\infra\10-task.ps1 -Job grant-subscription -Email persona@ejemplo.com -Days 30
  ```

## Volver atrás

- **La API:** `09-service.ps1 -ImageTag <tag anterior>`. ECR guarda las últimas 10 imágenes. Express
  Mode despliega en canario con alarma de 5XX: un despliegue que rompe se revierte solo.
- **El frontend:** `11-frontend-deploy.ps1 -Ref <tag anterior>`.
- **Una migración:** no hay tarea de `downgrade` a propósito. Si una migración rompió datos, se
  restaura la base: RDS tiene recuperación a un punto en el tiempo de los últimos 7 días (consola →
  RDS → `nureon-db` → *Restore to point in time*, a una instancia nueva) y después se apunta el
  servicio a ella. Es un paso a mano y deliberado.

## La contraseña de la base

RDS rota el secreto maestro cada 365 días (`02-database.ps1`). Las tareas leen la contraseña al
arrancar: después de una rotación hay que forzar un despliegue para que la tomen.

```powershell
aws ecs update-service --cluster nureon --service nureon-api --force-new-deployment --profile nureon-deploy --region us-east-2
```

## Apagar todo

```powershell
powershell -File backend\infra\teardown.ps1 -Confirm apagar-nureon
```

Borra en orden inverso lo que crearon los pasos 1 a 11: el servicio de Express Mode con su ALB,
security groups y certificado; el cluster; la base, dejando un snapshot final `nureon-db-final-<fecha>`
salvo con `-SkipFinalSnapshot`; la red; el secreto de la app, recuperable 7 días; el repositorio; el
log group; los roles; la distribución, el OAC y el bucket. Tarda ~20 minutos. No toca Cognito, SES ni el
usuario `nureon-deploy`. Al final corre `status.ps1`.

El snapshot cuesta US$0,095 por GB-mes (menos de US$2 por mes); conserva los datos del piloto. Se borra
a mano cuando no haga falta.

## Qué hay creado

```powershell
powershell -File backend\infra\status.ps1
```

Lista cada recurso, su estado y su costo mensual, y los créditos que quedan.

## Costo y créditos

Precios de lista de `us-east-2` (API de precios, 2026-10-18), 730 horas por mes:

| Recurso | US$/mes |
|---|---|
| Fargate, 1 tarea de 0,5 vCPU y 1 GB (US$0,04048 por vCPU-h + US$0,004445 por GB-h) | 18,02 |
| ALB de Express Mode (US$0,0225/h + LCU) | ~16,5–17 |
| IPv4 públicas: 2 del ALB + 1 por tarea (US$0,005/h) | 10,95 |
| RDS `db.t4g.micro` + 20 GB gp3 | 13,98 |
| Secrets Manager (2 secretos) | 0,80 |
| ECR, logs, S3, CloudFront (dentro del nivel gratuito) | < 1 |
| **Total con 1 tarea** | **~61** (~79 con 2) |

Cada despliegue en sí cuesta menos de US$0,01 (tarea canaria unos minutos, tareas sueltas por
segundo). La cuenta está en el **plan gratuito, con US$100 de crédito** (2026-10-18): a este ritmo
alcanza para unas 7 semanas. Cuando se terminan, AWS cierra la cuenta entera, user pool de Cognito
incluido, y la borra si en 90 días no se pasa a plan pago. Por eso se despliega cerca de la demo, y al
retomar se vuelve a mirar `00-check.ps1`. Para estirar: Fargate en ARM64 (~20% menos) o apagar con
`teardown.ps1` entre la demo y lo que siga.

## Cuentas de humo

Cada corrida de `12-smoke.ps1` registra y borra una cuenta reconocible
(`nureon-smoke-<fecha>@smoke.nureon.invalid`). Borrarla la anonimiza pero conserva su intento y sus
respuestas: **hay que excluir estos ids de cualquier análisis.**

| Fecha (UTC) | `users.id` | Intento |
|---|---|---|
| — | — | — |

## Verificación manual

```powershell
$p = @('--profile', 'nureon-deploy', '--region', 'us-east-2')
# La base no es pública, y su security group sólo acepta 5432 desde el del servicio:
aws rds describe-db-instances --db-instance-identifier nureon-db --query 'DBInstances[0].{public:PubliclyAccessible,subnets:DBSubnetGroup.Subnets[].SubnetIdentifier}' @p
aws ec2 describe-security-groups --filters Name=group-name,Values=nureon-db --query 'SecurityGroups[0].IpPermissions' @p
# Las subnets de la base no tienen ruta a internet:
aws ec2 describe-route-tables --filters Name=tag:Name,Values=nureon-private --query 'RouteTables[0].Routes' @p
# El security group del servicio sólo acepta tráfico del ALB:
aws ecs describe-services --cluster nureon --services nureon-api --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' @p
aws ec2 describe-security-groups --group-ids <sg del servicio> --query 'SecurityGroups[0].IpPermissions' @p
# El endpoint de la base no resuelve a una IP pública, y desde afuera no conecta:
Resolve-DnsName <endpoint de nureon-db>
Test-NetConnection <endpoint de nureon-db> -Port 5432
# Logs sin emails, tokens ni contraseñas:
powershell -File backend\infra\logs.ps1 -Minutes 60 -Scan
```
