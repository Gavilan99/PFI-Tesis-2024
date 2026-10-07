import uuid
from typing import Annotated, Any

from pydantic import StringConstraints, model_validator

from app.blueprints.schemas import ApiModel, ApiOutput
from app.db.models.enums import AccountType
from app.exceptions import EmailNotEditable


class UserOut(ApiOutput):
    """The `User` of user.model.ts, field by field. Nothing else of the row leaves the server."""

    id: uuid.UUID
    display_name: str | None
    email: str | None
    account_type: AccountType | None
    age_range: str | None
    gender: str | None
    country: str | None
    profession_context: str | None


def _text(max_length: int):
    return Annotated[str, StringConstraints(strip_whitespace=True, max_length=max_length)]


class UpdateProfileIn(ApiModel):
    """`UpdateProfileInput`: every field optional, and no field outside it. Email is not editable."""

    display_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)] = None
    account_type: AccountType | None = None
    age_range: _text(32) | None = None
    gender: _text(64) | None = None
    country: _text(64) | None = None
    profession_context: _text(255) | None = None

    @model_validator(mode="before")
    @classmethod
    def _drop_ignored_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "email" in data:
                raise EmailNotEditable()
            # The frontend's updateProfile(userId, ...) may carry it; identity comes from the token.
            data = {key: value for key, value in data.items() if key != "userId"}
        return data

    def changes(self) -> dict[str, Any]:
        """Only the fields the client sent. An empty optional text means "cleared"."""
        changes = {name: getattr(self, name) for name in self.model_fields_set}
        for name, value in changes.items():
            if value == "":
                changes[name] = None
        return changes
