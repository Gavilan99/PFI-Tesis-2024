# The backend image. Built from the repository root, so the bank CSV in research/ can go in:
#
#     docker build -f backend/Dockerfile --build-arg GIT_REF=$(git describe --tags --always --dirty) -t nureon-api .
#
# What goes in is an allowlist (Dockerfile.dockerignore): the app, migrations, scripts and the bank.
# Never .env, tests, .venv or credentials. app/ml/artifacts/ (the trained models, not versioned) goes
# in with app/ when it exists on the build machine, and is simply absent when it does not.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/alembic.ini backend/wsgi.py ./
COPY backend/migrations ./migrations
COPY backend/scripts ./scripts
COPY backend/app ./app
# The bank the product loads as version 1. The load runs as a one-off task inside the VPC, from here.
COPY ["research/bank/NureonAI Prototype v4.1.2.csv", "./bank/"]

RUN useradd --system --no-create-home --uid 10001 nureon
USER nureon

# Which commit or tag this image was built from, to know what runs.
ARG GIT_REF=unknown
LABEL org.opencontainers.image.revision=$GIT_REF \
      org.opencontainers.image.title="nureon-api"

EXPOSE 8000

# One worker with threads: the app mostly waits on Postgres and Cognito, and one process per task keeps
# one contact-form rate counter per task. Access log off: the app logs what it needs, without bodies.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gthread", "--workers", "1", "--threads", "8", \
     "--timeout", "30", "--graceful-timeout", "25", "wsgi:app"]
