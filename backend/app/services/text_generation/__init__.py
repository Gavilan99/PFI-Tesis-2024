from app.services.text_generation.base import TextGenerationFailed, TextGenerator
from app.services.text_generation.bedrock import BedrockTextGenerator
from app.services.text_generation.local import LocalTextGenerator

__all__ = [
    "BedrockTextGenerator",
    "LocalTextGenerator",
    "TextGenerationFailed",
    "TextGenerator",
    "build_text_generator",
]


def build_text_generator(config) -> TextGenerator | None:
    """`None` for TEXT_GENERATOR=pregenerated (Feature 19): there is no model to call, only the
    pregenerated content (`app.services.text_generation.pregenerated_content`), which
    `app.services.personalized_descriptions` reads directly instead of through this interface."""
    if config.TEXT_GENERATOR == "bedrock":
        return BedrockTextGenerator(
            region=config.BEDROCK_REGION,
            model_id=config.BEDROCK_MODEL_ID,
            timeout_seconds=config.TEXT_GENERATION_TIMEOUT_SECONDS,
            profile=config.AWS_PROFILE,
        )
    if config.TEXT_GENERATOR == "pregenerated":
        return None
    return LocalTextGenerator()
