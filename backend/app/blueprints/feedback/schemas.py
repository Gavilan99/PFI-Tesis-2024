import uuid
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

from app.blueprints.schemas import ApiModel

COMMENT_MAX_LENGTH = 2000
CONTACT_NAME_MAX_LENGTH = 100
CONTACT_EMAIL_MAX_LENGTH = 254
CONTACT_MESSAGE_MIN_LENGTH = 10  # the /contacto form's own minimum
CONTACT_MESSAGE_MAX_LENGTH = 5000


class SubmitFeedbackIn(ApiModel):
    """`SubmitFeedbackInput`, exactly: the three fields, `null` where the contract allows it."""

    test_attempt_id: uuid.UUID | None
    # Strict: 4.5, "4" and true are not ratings.
    rating: Annotated[int, Field(strict=True, ge=1, le=5)]
    comment: Annotated[str, StringConstraints(strip_whitespace=True, max_length=COMMENT_MAX_LENGTH)] | None

    @field_validator("comment")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return value or None


# Stricter than the login one: this address goes into a mail header. Plain ASCII addresses only.
ContactEmail = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        max_length=CONTACT_EMAIL_MAX_LENGTH,
        pattern=r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$",
    ),
]


class SubmitContactMessageIn(ApiModel):
    """`SubmitContactMessageInput`, exactly."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CONTACT_NAME_MAX_LENGTH)]
    email: ContactEmail
    message: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=CONTACT_MESSAGE_MIN_LENGTH, max_length=CONTACT_MESSAGE_MAX_LENGTH
        ),
    ]
