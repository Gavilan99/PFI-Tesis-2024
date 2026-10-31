"""In-process text generator, for tests and local development only. Calls no model.

Not a production mode: config refuses `TEXT_GENERATOR=local` with `APP_ENV=production`. The answer
follows the same FORTALEZAS/TENSIONES/CRECIMIENTO/ESTRES format
`app.services.personalized_descriptions` asks Bedrock for, built around a short hash of the user
prompt it was given — so it demonstrably varies with the eneatype, the account type and the rest of
the profile, without this module having to parse the prompt back apart to prove it. `fail` makes
every call raise TextGenerationFailed, to exercise the "unavailable" path in tests.
"""

import hashlib

from app.services.text_generation.base import TextGenerationFailed, TextGenerator

LOCAL_TEXT_MODEL_ID = "local-text-1"


def _fingerprint(user_prompt: str) -> str:
    return hashlib.sha256(user_prompt.encode("utf-8")).hexdigest()[:8]


class LocalTextGenerator(TextGenerator):
    model_id = LOCAL_TEXT_MODEL_ID

    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.calls = 0

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        if self.fail:
            raise TextGenerationFailed()
        marker = _fingerprint(user_prompt)
        return (
            "FORTALEZAS:\n"
            f"Fortaleza de ejemplo uno del doble local de texto (marca {marker}).\n"
            f"Fortaleza de ejemplo dos del doble local de texto (marca {marker}).\n"
            f"Fortaleza de ejemplo tres del doble local de texto (marca {marker}).\n"
            "TENSIONES:\n"
            f"Tensión de ejemplo uno del doble local de texto (marca {marker}).\n"
            f"Tensión de ejemplo dos del doble local de texto (marca {marker}).\n"
            f"Tensión de ejemplo tres del doble local de texto (marca {marker}).\n"
            "CRECIMIENTO:\n"
            "Párrafo de ejemplo de crecimiento, generado por el doble local de texto para desarrollo "
            f"y tests, no por un modelo real (marca {marker}).\n"
            "ESTRES:\n"
            "Párrafo de ejemplo de estrés, generado por el doble local de texto para desarrollo y "
            f"tests, no por un modelo real (marca {marker})."
        )
