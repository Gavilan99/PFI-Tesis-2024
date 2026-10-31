"""Amazon Bedrock, reached from the backend with boto3's Converse API: one call, with the configured
model (BEDROCK_MODEL_ID) and a fixed, short answer budget.

https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html

Nothing about the request or the response is logged: see app.services.personalized_descriptions for
what may and may not reach a log line. Retries are disabled (`total_max_attempts: 1`): the caller has
its own timeout budget (TEXT_GENERATION_TIMEOUT_SECONDS) and a retry here could run well past it —
note that `{"max_attempts": N}` is *not* the same knob: botocore's legacy retry mode counts it as
retries after the first attempt, so `max_attempts: 1` would still allow one retry.
"""

import logging

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.services.text_generation.base import TextGenerationFailed, TextGenerator

logger = logging.getLogger(__name__)

# The parser allows up to 6 lines of 200 chars each for FORTALEZAS/TENSIONES plus two 700-char
# paragraphs — close to 3800 characters of valid output. A maximal-but-otherwise-valid answer must
# never be cut off and rejected for it, so the budget stays generous above that ceiling.
MAX_TOKENS = 1500
TEMPERATURE = 0.5
# Reaching the regional endpoint should be near-instant; the configured budget
# (TEXT_GENERATION_TIMEOUT_SECONDS) belongs to waiting for the model's answer, not the connection.
CONNECT_TIMEOUT_SECONDS = 5


def _error_code(exc: Exception) -> str:
    if isinstance(exc, ClientError):
        return exc.response.get("Error", {}).get("Code", "")
    return type(exc).__name__


class BedrockTextGenerator(TextGenerator):
    def __init__(
        self, region: str, model_id: str, *, timeout_seconds: int, profile: str | None, client=None
    ):
        self.model_id = model_id
        if client is None:
            # Explicit profile from config, never boto3's implicit choice. `None` only where config
            # allows it (deployed, with role credentials and no profile file).
            if profile == "default":
                raise ValueError("The 'default' AWS profile is never used by this backend.")
            client = boto3.Session(profile_name=profile, region_name=region).client(
                "bedrock-runtime",
                config=Config(
                    connect_timeout=CONNECT_TIMEOUT_SECONDS,
                    read_timeout=timeout_seconds,
                    retries={"total_max_attempts": 1},
                ),
            )
        self._client = client

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.converse(
                modelId=self.model_id,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_prompt}]}],
                inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": TEMPERATURE},
            )
        except (ClientError, BotoCoreError) as exc:
            logger.error("Bedrock Converse failed: %s", _error_code(exc))
            raise TextGenerationFailed() from None

        if response.get("stopReason") != "end_turn":
            logger.error("Bedrock Converse stopped with reason %s", response.get("stopReason"))
            raise TextGenerationFailed()

        blocks = response.get("output", {}).get("message", {}).get("content", [])
        text = "".join(block.get("text", "") for block in blocks).strip()
        if not text:
            logger.error("Bedrock Converse answered with no text")
            raise TextGenerationFailed()
        return text
