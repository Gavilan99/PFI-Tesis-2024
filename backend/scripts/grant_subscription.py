#!/usr/bin/env python3
"""
Give an account the paid tier for N days by hand: a subscription row with NO payment behind it.

    python scripts/grant_subscription.py --email persona@ejemplo.com --days 30
    python scripts/grant_subscription.py --email persona@ejemplo.com --days 30 --dry-run

For development and for the accounts of the user tests, until checkout and the Mercado Pago webhook
exist (Feature 6). Writes one `subscriptions` row: tier `individual`, status `active`, period from now
to now + N days, `mercadopago_subscription_id` NULL, and no `payments` row. That NULL is how a manual
grant is told apart from a paid one forever.

In production it runs as a one-off task: `backend/infra/10-task.ps1 -Job grant-subscription`. The
output names the account by its id, never by its email, because it ends up in CloudWatch.
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run as a file from backend/

from app.db.models.enums import SubscriptionTier  # noqa: E402
from app.repositories import subscription_repository, user_repository  # noqa: E402
from scripts._db import database_url, describe, open_session, utf8_output  # noqa: E402

MAX_DAYS = 366


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Alta manual de una suscripción, sin pago asociado.")
    parser.add_argument("--email", required=True, help="Email de la cuenta (no distingue mayúsculas).")
    parser.add_argument("--days", required=True, type=int, help=f"Días de vigencia, de 1 a {MAX_DAYS}.")
    parser.add_argument("--dry-run", action="store_true", help="Mostrar lo que haría, sin guardar.")
    args = parser.parse_args(argv)
    utf8_output()

    if not 1 <= args.days <= MAX_DAYS:
        print(f"--days tiene que estar entre 1 y {MAX_DAYS}; vale {args.days}.", file=sys.stderr)
        return 2

    url = database_url()
    with open_session(url) as session:
        user = user_repository.get_live_by_email(session, args.email.strip().lower())
        if user is None:
            print(f"Base: {describe(url)}", file=sys.stderr)
            print("No hay ninguna cuenta viva con ese email: no se dio de alta nada.", file=sys.stderr)
            return 1
        start = datetime.now(timezone.utc)
        end = start + timedelta(days=args.days)
        subscription = subscription_repository.insert_manual(
            session, user.id, tier=SubscriptionTier.INDIVIDUAL, start=start, end=end
        )
        # Read before committing: the session closes right after, and its objects expire.
        user_id, subscription_id = user.id, subscription.id
        if args.dry_run:
            session.rollback()
        else:
            session.commit()

    print(f"Base: {describe(url)}")
    print("ALTA MANUAL DE SUSCRIPCIÓN, SIN PAGO ASOCIADO (sin Mercado Pago, sin fila en payments).")
    if args.dry_run:
        print("SIMULACIÓN (--dry-run): no se guardó nada.")
    else:
        print(f"Suscripción {subscription_id}")
    print(f"Cuenta users.id = {user_id} · tier individual, activa · "
          f"del {start:%Y-%m-%d %H:%M} al {end:%Y-%m-%d %H:%M} UTC ({args.days} días)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
