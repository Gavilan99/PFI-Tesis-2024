"""Tiers. The server decides; the client can never send one.

- A person has the paid tier when they have a `subscriptions` row with `status = active` and a
  `current_period_end` that is empty or in the future. Checkout and the Mercado Pago webhook that
  create those rows are Feature 6; until then they come from scripts/grant_subscription.py.
- The first cut of the test is the free level; the second and third require the paid tier.
- An attempt starts `free_reduced` and becomes `paid_full` when it continues to a paid cut (decision
  of 17/10: whoever pays after cut 1 goes on with the same attempt).
"""

import uuid
from datetime import datetime, timezone

from app.db.models.enums import AttemptTier
from app.repositories import subscription_repository

FREE_CUTS = 1  # cuts 1..FREE_CUTS are the free level


def new_attempt_tier() -> AttemptTier:
    return AttemptTier.FREE_REDUCED


def required_tier(cut_number: int) -> AttemptTier:
    return AttemptTier.FREE_REDUCED if cut_number <= FREE_CUTS else AttemptTier.PAID_FULL


def has_paid_tier(session, user_id: uuid.UUID, now: datetime | None = None) -> bool:
    return subscription_repository.has_active(session, user_id, now or datetime.now(timezone.utc))


def may_take_cut(session, user_id: uuid.UUID, cut_number: int) -> bool:
    return required_tier(cut_number) is AttemptTier.FREE_REDUCED or has_paid_tier(session, user_id)
