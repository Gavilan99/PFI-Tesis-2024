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

## Variables de entorno

Ver [.env.example](./.env.example). En `production`, `SECRET_KEY`, `DATABASE_URL` y
`CORS_ALLOWED_ORIGINS` son obligatorias: si falta alguna, la app no arranca y lo dice por nombre.
En `development` y `test` tienen valores por defecto de uso local, no aptos para producción.
