"""POST /api/contact-messages: mailed to our inbox through the mail seam, never stored, never logged.

Runs against the local double (`MAIL_SENDER=local`); the SES sender is checked against a fake client.
"""

import uuid
from email import message_from_bytes
from email.policy import default as default_policy
from email.utils import getaddresses, parseaddr

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from sqlalchemy import text

from app.blueprints.feedback.schemas import (
    CONTACT_EMAIL_MAX_LENGTH,
    CONTACT_MESSAGE_MAX_LENGTH,
    CONTACT_NAME_MAX_LENGTH,
)
from app.exceptions import ContactUnavailable
from app.services.contact import build_contact_mail
from app.services.mail import SesMailSender
from app.services.rate_limit import SlidingWindowLimiter
from tests.auth_helpers import assert_error
from tests.log_helpers import captured_logs  # noqa: F401  (fixture)

URL = "/api/contact-messages"
# Every header the mail carries, and no other. EmailMessage.set_content adds the last three.
MAIL_HEADERS = {"From", "To", "Reply-To", "Subject", "Content-Type", "Content-Transfer-Encoding", "MIME-Version"}


def _body(**overrides) -> dict:
    return {
        "name": "Ana Pérez",
        "email": "ana.perez@example.test",
        "message": "Hola, quería saber si el test sirve para equipos de trabajo.",
        **overrides,
    }


def _received(mailbox):
    """The one mail the double holds, parsed back from the bytes SES would have been given."""
    [message] = mailbox.sent
    return message_from_bytes(message.as_bytes(), policy=default_policy)


def _post(api, body, origin="203.0.113.10"):
    return api.post(URL, json=body, environ_base={"REMOTE_ADDR": origin})


# --- the mail -----------------------------------------------------------------------------------


def test_a_valid_message_reaches_the_inbox_with_reply_to_the_writer(api, app, mailbox):
    response = _post(api, _body())

    assert response.status_code == 204
    assert response.get_data() == b""
    mail = _received(mailbox)
    assert set(mail.keys()) == MAIL_HEADERS
    assert parseaddr(mail["To"])[1] == app.config["CONTACT_MAIL_TO"]
    assert parseaddr(mail["From"])[1] == app.config["CONTACT_MAIL_FROM"]
    assert getaddresses([mail["Reply-To"]]) == [("Ana Pérez", "ana.perez@example.test")]
    assert mail["Subject"] == "Contacto NureonAI: Ana Pérez"
    body = mail.get_content()
    assert "Nombre: Ana Pérez" in body
    assert "Email: ana.perez@example.test" in body
    assert _body()["message"] in body


def test_the_contact_route_is_public(api, mailbox):
    assert "Authorization" not in api.post(URL, json=_body()).request.headers
    assert len(mailbox.sent) == 1


def test_nothing_of_the_message_is_stored_or_logged(api, db_session, mailbox, captured_logs):
    marker = uuid.uuid4().hex
    body = _body(name=f"Nombre {marker}", email=f"m{marker}@example.test", message=f"Mensaje secreto {marker}.")

    assert _post(api, body).status_code == 204
    assert len(mailbox.sent) == 1

    # Every row of every table in the schema, as text.
    db_session.commit()
    tables = db_session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
    ).scalars().all()
    assert "feedback" in tables
    for table in tables:
        dump = db_session.execute(text(f'SELECT row_to_json(t)::text FROM "{table}" t')).scalars().all()
        assert not any(marker in row for row in dump), table

    assert captured_logs, "nothing was captured: the test would pass vacuously"
    for line in captured_logs:
        assert marker not in line


# --- header injection ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "Ana\r\nBcc: victima@example.test",
        "Ana\nSubject: otro asunto",
        "Ana\rCc: x@example.test",
        "Ana\r\n\r\nCuerpo inyectado",
        "Ana\x00\tPérez\x0b",
    ],
    ids=["crlf-bcc", "lf-subject", "cr-cc", "blank-line", "other-controls"],
)
def test_a_name_with_line_breaks_adds_no_header(api, mailbox, name):
    assert _post(api, _body(name=name)).status_code == 204

    mail = _received(mailbox)
    assert set(mail.keys()) == MAIL_HEADERS
    assert [mail.get_all(header) for header in ("To", "Reply-To", "Subject")] == [
        [mail["To"]], [mail["Reply-To"]], [mail["Subject"]],
    ]
    for header in MAIL_HEADERS:
        assert "\r" not in mail[header] and "\n" not in mail[header]
    assert getaddresses([mail["Reply-To"]])[0][1] == "ana.perez@example.test"
    # The name survives, on one line.
    assert mail["Subject"].startswith("Contacto NureonAI: Ana")


def test_the_mail_builder_keeps_header_values_on_one_line_whatever_it_is_given():
    mail = build_contact_mail(
        name="Ana\r\nBcc: victima@example.test",
        email="ana@example.test\r\nCc: otro@example.test",
        message="línea 1\nlínea 2",
        mail_to="destino@example.test",
        mail_from="destino@example.test",
    )
    raw = mail.as_bytes()
    parsed = message_from_bytes(raw, policy=default_policy)
    assert set(parsed.keys()) == MAIL_HEADERS
    header_block = raw.split(b"\r\n\r\n", 1)[0].decode()
    assert "\nBcc:" not in header_block and "\nCc:" not in header_block
    # Line breaks belong in the body, and stay there (as CRLF, the mail's line ending).
    assert "línea 1\r\nlínea 2" in parsed.get_content()


# --- validation ---------------------------------------------------------------------------------


def test_a_message_longer_than_the_maximum_is_rejected(api, mailbox):
    assert _post(api, _body(message="x" * CONTACT_MESSAGE_MAX_LENGTH)).status_code == 204
    response = _post(api, _body(message="x" * (CONTACT_MESSAGE_MAX_LENGTH + 1)))
    assert_error(response, 400, "VALIDATION_ERROR", "Los datos enviados no son válidos.")
    assert len(mailbox.sent) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * (CONTACT_NAME_MAX_LENGTH + 1)},
        {"email": "no-es-un-email"},
        {"email": "ana@example"},
        {"email": "ana perez@example.test"},
        {"email": "ana@example.test\r\nBcc: x@example.test"},
        {"email": "ana,otra@example.test"},
        {"email": "a" * (CONTACT_EMAIL_MAX_LENGTH - len("@example.test") + 1) + "@example.test"},
        {"message": "corto"},
        {"message": None},
    ],
    ids=[
        "empty-name", "blank-name", "long-name", "not-an-email", "no-tld", "space", "crlf-email", "comma",
        "long-email", "short-message", "null-message",
    ],
)
def test_malformed_fields_are_rejected_and_nothing_is_sent(api, mailbox, overrides):
    assert_error(_post(api, _body(**overrides)), 400, "VALIDATION_ERROR")
    assert mailbox.sent == []


@pytest.mark.parametrize(
    "body",
    [{"name": "Ana", "email": "ana@example.test"}, {**_body(), "phone": "1234"}, "texto", None],
    ids=["missing-field", "extra-field", "string", "no-body"],
)
def test_the_body_is_submit_contact_message_input_and_nothing_else(api, mailbox, body):
    assert_error(_post(api, body), 400, "VALIDATION_ERROR")
    assert mailbox.sent == []


# --- rate limit ---------------------------------------------------------------------------------


def test_passing_the_limit_per_origin_is_429_and_sends_nothing_more(api, app, mailbox):
    limit = app.config["CONTACT_RATE_LIMIT"]
    for _ in range(limit):
        assert _post(api, _body(), origin="198.51.100.7").status_code == 204

    response = _post(api, _body(), origin="198.51.100.7")

    assert_error(
        response, 429, "CONTACT_RATE_LIMITED", "Enviaste varios mensajes seguidos. Probá de nuevo más tarde."
    )
    assert len(mailbox.sent) == limit
    # Another origin is not affected.
    assert _post(api, _body(), origin="198.51.100.8").status_code == 204


def test_rejected_bodies_do_not_count_towards_the_limit(api, app, mailbox):
    for _ in range(app.config["CONTACT_RATE_LIMIT"] + 3):
        _post(api, _body(message="corto"))
    assert _post(api, _body()).status_code == 204


def test_the_window_forgets_old_hits():
    now = [0.0]
    limiter = SlidingWindowLimiter(2, 60, clock=lambda: now[0])
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")
    now[0] = 59.9
    assert not limiter.allow("a")
    now[0] = 60.0
    assert limiter.allow("a")


# --- when sending fails -------------------------------------------------------------------------


def test_a_failed_send_is_503_in_spanish_keeps_nothing_and_can_be_retried(api, mailbox, monkeypatch):
    original_send = mailbox.send

    def unavailable(message):
        raise ContactUnavailable()

    monkeypatch.setattr(mailbox, "send", unavailable)
    response = _post(api, _body())
    assert_error(response, 503, "CONTACT_UNAVAILABLE", "No pudimos enviar tu mensaje. Probá de nuevo en unos minutos.")
    assert mailbox.sent == []

    monkeypatch.setattr(mailbox, "send", original_send)
    assert _post(api, _body()).status_code == 204
    assert len(mailbox.sent) == 1


# --- the SES sender -----------------------------------------------------------------------------


class _FakeSes:
    def __init__(self, error: Exception | None = None):
        self.calls: list[dict] = []
        self.error = error

    def send_email(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return {"MessageId": "fake-id"}


def _mail():
    return build_contact_mail(
        name="Ana", email="ana@example.test", message="Un mensaje de prueba.",
        mail_to="destino@example.test", mail_from="remitente@example.test",
    )


def test_ses_gets_the_raw_mail_with_the_envelope_from_config():
    client = _FakeSes()
    mail = _mail()

    SesMailSender("us-east-2", profile="nureon", client=client).send(mail)

    [call] = client.calls
    assert call == {
        "FromEmailAddress": "remitente@example.test",
        "Destination": {"ToAddresses": ["destino@example.test"]},
        "Content": {"Raw": {"Data": mail.as_bytes()}},
    }


@pytest.mark.parametrize(
    "error",
    [
        ClientError(
            {"Error": {"Code": "MessageRejected", "Message": "Email address is not verified: ana@example.test"}},
            "SendEmail",
        ),
        EndpointConnectionError(endpoint_url="https://email.us-east-2.amazonaws.com"),
    ],
    ids=["rejected", "unreachable"],
)
def test_a_ses_failure_becomes_contact_unavailable_and_logs_only_the_code(error, captured_logs):
    with pytest.raises(ContactUnavailable):
        SesMailSender("us-east-2", profile="nureon", client=_FakeSes(error)).send(_mail())
    assert any("SES SendEmail failed" in line for line in captured_logs)
    for line in captured_logs:
        assert "ana@example.test" not in line
        assert "Un mensaje de prueba" not in line


def test_the_default_aws_profile_is_refused():
    with pytest.raises(ValueError, match="default"):
        SesMailSender("us-east-2", profile="default")
