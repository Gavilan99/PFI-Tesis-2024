"""Database enum types and the canonical vocabulary (see "Vocabulario canónico" in CLAUDE.md).

Each Python enum maps to a Postgres enum type of the same values. `group_label` is a varchar in the
PDR, so it is not a Postgres enum; its allowed values are enforced with a CHECK instead.
"""

import enum

import sqlalchemy as sa


class AccountType(enum.StrEnum):
    INDIVIDUAL = "individual"
    RRHH = "rrhh"
    SALUD = "salud"


class GroupingSystem(enum.StrEnum):
    INTELLIGENCE_CENTERS = "intelligence_centers"
    HORNEVIAN = "hornevian"
    HARMONIC = "harmonic"
    OBJECT_RELATIONS = "object_relations"


class QuestionType(enum.StrEnum):
    # Bank v1 only uses SCENARIO (3 options) and MULTIPLE_CHOICE (Likert, 5 ordered options).
    # ORDERING and TEXT are valid in the schema but out of scope.
    MULTIPLE_CHOICE = "multiple_choice"
    ORDERING = "ordering"
    TEXT = "text"
    SCENARIO = "scenario"


class AttemptTier(enum.StrEnum):
    FREE_REDUCED = "free_reduced"
    PAID_FULL = "paid_full"


class AttemptStatus(enum.StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SubscriptionTier(enum.StrEnum):
    INDIVIDUAL = "individual"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    PRO = "pro"
    UNLIMITED = "unlimited"


class SubscriptionStatus(enum.StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


GROUPS_BY_SYSTEM: dict[GroupingSystem, tuple[str, str, str]] = {
    GroupingSystem.INTELLIGENCE_CENTERS: ("gut", "heart", "head"),
    GroupingSystem.HORNEVIAN: ("assertive", "compliant", "withdrawn"),
    GroupingSystem.HARMONIC: ("positive_outlook", "competency", "reactive"),
    GroupingSystem.OBJECT_RELATIONS: ("attachment", "frustration", "rejection"),
}

GROUP_LABELS: tuple[str, ...] = tuple(g for groups in GROUPS_BY_SYSTEM.values() for g in groups)


def _pg_enum(enum_cls: type[enum.Enum], name: str) -> sa.Enum:
    return sa.Enum(
        enum_cls,
        name=name,
        values_callable=lambda members: [m.value for m in members],
        validate_strings=True,
    )


# One instance per database type, shared by every column that uses it.
account_type_enum = _pg_enum(AccountType, "account_type")
grouping_system_enum = _pg_enum(GroupingSystem, "grouping_system")
question_type_enum = _pg_enum(QuestionType, "question_type")
attempt_tier_enum = _pg_enum(AttemptTier, "attempt_tier")
attempt_status_enum = _pg_enum(AttemptStatus, "attempt_status")
subscription_tier_enum = _pg_enum(SubscriptionTier, "subscription_tier")
subscription_status_enum = _pg_enum(SubscriptionStatus, "subscription_status")

ALL_ENUM_TYPES = (
    account_type_enum,
    grouping_system_enum,
    question_type_enum,
    attempt_tier_enum,
    attempt_status_enum,
    subscription_tier_enum,
    subscription_status_enum,
)
