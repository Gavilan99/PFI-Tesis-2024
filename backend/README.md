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
