"""Which tier a new attempt gets. The server decides; the client can never send one.

Seam for Feature 6 (payments): there the tier comes from the user's active subscription. Until then,
every attempt is `free_reduced`. Only this function's body changes when that lands.
"""

from app.db.models import User
from app.db.models.enums import AttemptTier


def resolve_attempt_tier(user: User) -> AttemptTier:
    return AttemptTier.FREE_REDUCED
