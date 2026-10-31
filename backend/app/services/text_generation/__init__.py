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


def build_text_generator(config) -> TextGenerator:
    if config.TEXT_GENERATOR == "bedrock":
        return BedrockTextGenerator(
            region=config.BEDROCK_REGION,
            model_id=config.BEDROCK_MODEL_ID,
            timeout_seconds=config.TEXT_GENERATION_TIMEOUT_SECONDS,
            profile=config.AWS_PROFILE,
        )
    return LocalTextGenerator()
