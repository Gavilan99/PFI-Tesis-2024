from typing import Annotated

from pydantic import Field, SecretStr, StrictBool, StringConstraints

from app.blueprints.schemas import ApiModel, ApiOutput
from app.blueprints.users.schemas import UserOut

# Deliberately loose: the provider is the authority on what an email is. This only rejects what is
# obviously not one, before spending a call.
Email = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
]


class RegisterIn(ApiModel):
    """`RegisterInput`, exactly. The password is a SecretStr so no repr or error can print it.

    `consentAccepted` defaults to false so that a body without it gets CONSENT_REQUIRED, the message
    that says what is missing, rather than the generic validation error. Strict: only a JSON boolean.
    """

    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)]
    email: Email
    password: Annotated[SecretStr, Field(min_length=8, max_length=256)]
    consent_accepted: StrictBool = False


class LoginIn(ApiModel):
    """`LoginInput`, exactly."""

    email: Email
    password: Annotated[SecretStr, Field(min_length=1, max_length=256)]


class AuthOut(ApiOutput):
    """The `User` plus the access token beside it (field names agreed on 06-10 for Feature 7)."""

    user: UserOut
    access_token: str
    expires_in: int
