# NureonAI — Backend

Servicio Flask. Ver [CLAUDE.md](./CLAUDE.md) para el stack, la estructura y las convenciones.

## Requisitos

- Python 3.11
- Docker y Docker Compose (Postgres local)

## Levantar el entorno de desarrollo

```bash
cp .env.example .env
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements-dev.txt

docker compose up -d
alembic upgrade head

python wsgi.py
```

`GET http://localhost:5000/api/health` responde sin tocar la base. `GET /api/health/ready` sí la
toca y devuelve 503 si no responde.

## Banco de preguntas

El relleno se carga como **versión 0** del cuestionario. Dice en su propio texto que es relleno y
tiene la forma del banco v1 (200 preguntas, 50 por sistema, 163 de escenario y 37 Likert):

```bash
python scripts/seed_filler_bank.py            # idempotente; activa la versión 0 si no hay otra activa
python scripts/seed_filler_bank.py --dry-run
```

El banco real entra por su CSV, una fila por opción. Los encabezados se ajustan en `COLUMNS`, arriba
del script; si no coinciden, el script lo dice por nombre antes de leer nada:

```bash
python scripts/import_question_bank.py --csv banco.csv --version 1 --dry-run
python scripts/import_question_bank.py --csv banco.csv --version 1 --activate
```

Reimportar una versión sin respuestas no duplica: la deja igual al CSV. Una versión que ya tiene
respuestas no se toca más: reimportarla se rechaza entera, y un banco cambiado se carga como versión
nueva. `--activate` desactiva las demás versiones en la misma transacción.

## Correr los tests

Con el Postgres del compose arriba (crea `nureon_dev` y `nureon_test`):

```bash
docker compose up -d
pytest
```

## Clasificación y resultado

Cerrar un intento calcula su resultado con el clasificador que elige `CLASSIFIER_BACKEND`:

- `stub` (por defecto en `development` y `test`): conteo por grupo. Determinístico. No es ML.
- `legacy_tree`: el árbol de decisión de 2024, el del documento original.
- `trained`: los cuatro Random Forest. Todavía no existe: la app no arranca con este valor.

Cambiar de uno a otro es cambiar la variable y reiniciar. En `production` es obligatoria. Detalle y
mediciones en [app/ml/README.md](./app/ml/README.md).

```bash
python -m app.ml.pipeline         # el scaffold de cuatro clasificadores, sobre datos sintéticos
python -m app.ml.legacy.train     # reentrena el árbol de 2024 y lo compara con el guardado; no escribe
```

## Variables de entorno

Ver [.env.example](./.env.example). En `production`, `SECRET_KEY`, `DATABASE_URL` y
`CORS_ALLOWED_ORIGINS` son obligatorias: si falta alguna, la app no arranca y lo dice por nombre.
En `development` y `test` tienen valores por defecto de uso local, no aptos para producción.

## Cuentas e identidad

Registro, ingreso y perfil pasan por el backend; el navegador nunca habla con Cognito. El proveedor
de identidad se elige con `IDENTITY_PROVIDER`:

- `local` (por defecto en `development` y `test`): un doble en memoria. Las cuentas se pierden al
  reiniciar el proceso; las filas de `users` quedan. No es un modo de producción: con
  `APP_ENV=production` la app se niega a arrancar.
- `cognito`: el user pool real, con `COGNITO_USER_POOL_ID` y `COGNITO_APP_CLIENT_ID`. Por defecto en
  `production`.

Toda ruta exige `Authorization: Bearer <accessToken>` salvo las marcadas `@public` (health,
registro e ingreso). Contrato de los endpoints en [docs/api-contract.md](./docs/api-contract.md).
