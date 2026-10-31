"""The text-generation seam: one call that turns a system prompt and a user prompt into text.

Two implementations: `BedrockTextGenerator` (Amazon Bedrock, Converse API) and `LocalTextGenerator`
(a deterministic double for tests and local development, refused in production). Same pattern and
same reason as the identity, mail and payments seams: the suite never depends on Bedrock, and nothing
a generator returns is trusted as is — `app.services.personalized_descriptions` validates it before
it is ever stored or shown.
"""

from abc import ABC, abstractmethod


class TextGenerationFailed(Exception):
    """The provider could not produce usable text: a request error, a timeout, an empty answer, or a
    `stopReason` other than `end_turn`. The caller falls back to the "unavailable" status; nothing is
    stored."""


class TextGenerator(ABC):
    #: Identifies what produced the text (e.g. the Bedrock model id), stored alongside it so a later
    #: change to either regenerates instead of serving stale text under a new model.
    model_id: str

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """The model's answer to `user_prompt`, guided by `system_prompt`. Raises
        TextGenerationFailed on any failure; never returns an empty or partial answer."""
