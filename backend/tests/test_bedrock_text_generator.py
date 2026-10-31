"""The real generator, without the network: a fake bedrock-runtime client stands in. Nothing here
reaches Bedrock."""

import pytest
from botocore.exceptions import ClientError, ReadTimeoutError

from app.services.text_generation import BedrockTextGenerator, TextGenerationFailed
from tests.log_helpers import captured_logs  # noqa: F401  (fixture)

MODEL_ID = "amazon.nova-lite-v1:0"


class _FakeBedrock:
    def __init__(self, response=None, error: Exception | None = None):
        self.response, self.error = response, error
        self.calls: list[dict] = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


def _answer(text: str, stop_reason: str = "end_turn") -> dict:
    return {"stopReason": stop_reason, "output": {"message": {"content": [{"text": text}]}}}


def _generator(client) -> BedrockTextGenerator:
    return BedrockTextGenerator("us-east-2", MODEL_ID, timeout_seconds=10, profile="nureon", client=client)


def test_the_call_carries_the_model_the_prompts_and_the_configured_budget():
    fake = _FakeBedrock(_answer("Una descripción bien larga, para pasar la validación de longitud." * 5))
    text = _generator(fake).generate("prompt de sistema", "prompt de usuario")

    assert text == ("Una descripción bien larga, para pasar la validación de longitud." * 5)
    [call] = fake.calls
    assert call["modelId"] == MODEL_ID
    assert call["system"] == [{"text": "prompt de sistema"}]
    assert call["messages"] == [{"role": "user", "content": [{"text": "prompt de usuario"}]}]
    assert call["inferenceConfig"] == {"maxTokens": 700, "temperature": 0.5}


def test_a_client_error_is_text_generation_failed_and_logs_only_the_code(captured_logs):
    error = ClientError({"Error": {"Code": "ThrottlingException", "Message": "too many requests"}}, "Converse")
    with pytest.raises(TextGenerationFailed):
        _generator(_FakeBedrock(error=error)).generate("s", "u")
    assert any("ThrottlingException" in line for line in captured_logs)
    assert not any("too many requests" in line for line in captured_logs)


def test_a_timeout_is_text_generation_failed():
    error = ReadTimeoutError(endpoint_url="https://bedrock-runtime.us-east-2.amazonaws.com")
    with pytest.raises(TextGenerationFailed):
        _generator(_FakeBedrock(error=error)).generate("s", "u")


@pytest.mark.parametrize("stop_reason", ["max_tokens", "content_filtered", "stop_sequence"])
def test_a_stop_reason_other_than_end_turn_is_text_generation_failed(stop_reason):
    fake = _FakeBedrock(_answer("texto", stop_reason=stop_reason))
    with pytest.raises(TextGenerationFailed):
        _generator(fake).generate("s", "u")


def test_an_empty_answer_is_text_generation_failed():
    fake = _FakeBedrock(_answer("   "))
    with pytest.raises(TextGenerationFailed):
        _generator(fake).generate("s", "u")


def test_the_default_aws_profile_is_refused():
    with pytest.raises(ValueError, match="default"):
        BedrockTextGenerator("us-east-2", MODEL_ID, timeout_seconds=10, profile="default")


def test_the_prompts_never_reach_a_log_line(captured_logs):
    error = ClientError({"Error": {"Code": "ValidationException", "Message": "bad request"}}, "Converse")
    with pytest.raises(TextGenerationFailed):
        _generator(_FakeBedrock(error=error)).generate("prompt de sistema secreto", "prompt de usuario secreto")
    assert not any("secreto" in line for line in captured_logs)
