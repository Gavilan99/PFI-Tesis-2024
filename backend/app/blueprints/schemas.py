"""Shared pydantic plumbing: camelCase on the wire, snake_case in Python, converted here only."""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic.alias_generators import to_camel

from app.exceptions import ValidationFailed


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=False, extra="forbid")


class ApiOutput(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)


InputModel = TypeVar("InputModel", bound=ApiModel)


def parse_body(model: type[InputModel], body: Any) -> InputModel:
    """Validate a JSON body. A failure becomes ValidationFailed with nothing from the input attached:
    pydantic's own error text quotes the rejected values, and a password can be one of them."""
    if not isinstance(body, dict):
        raise ValidationFailed()
    try:
        return model.model_validate(body)
    except ValidationError:
        raise ValidationFailed() from None
