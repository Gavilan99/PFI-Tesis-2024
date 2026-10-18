"""The visitor's address behind the ALB, as the contact form's rate limit sees it.

The ALB appends the address it received the connection from to X-Forwarded-For. With
TRUSTED_PROXY_HOPS=1, ProxyFix takes that last entry and nothing before it: whatever a client writes
in the header itself never becomes its address.
"""

import pytest

from app import create_app
from app.services.mail import LocalMailSender

URL = "/api/contact-messages"
ALB = "10.0.1.25"  # every request reaches the app from the balancer's private address
BODY = {
    "name": "Ana Pérez",
    "email": "ana.perez@example.test",
    "message": "Hola, quería saber si el test sirve para equipos de trabajo.",
}


@pytest.fixture()
def behind_alb(monkeypatch):
    """An app configured for one trusted hop, with its own limiter and the local mail double."""
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "1")
    app = create_app("test")
    app.extensions["mail_sender"] = LocalMailSender()
    return app


def _post(app, forwarded_for: str):
    return app.test_client().post(
        URL, json=BODY, environ_base={"REMOTE_ADDR": ALB}, headers={"X-Forwarded-For": forwarded_for}
    )


def _exhaust(app, forwarded_for: str) -> None:
    for _ in range(app.config["CONTACT_RATE_LIMIT"]):
        assert _post(app, forwarded_for).status_code == 204
    assert _post(app, forwarded_for).status_code == 429


def test_two_visitors_behind_the_alb_have_separate_counters(behind_alb):
    _exhaust(behind_alb, "198.51.100.7")

    assert _post(behind_alb, "198.51.100.8").status_code == 204
    assert len(behind_alb.extensions["mail_sender"].sent) == behind_alb.config["CONTACT_RATE_LIMIT"] + 1


@pytest.mark.parametrize("spoofed", ["203.0.113.99", "unknown", "198.51.100.8, 203.0.113.1"])
def test_an_address_the_client_writes_in_the_header_does_not_change_its_own(behind_alb, spoofed):
    _exhaust(behind_alb, "198.51.100.7")

    # The client sent its own X-Forwarded-For; the ALB appended the real address after it.
    assert _post(behind_alb, f"{spoofed}, 198.51.100.7").status_code == 429


def test_without_trusted_hops_the_header_is_ignored(monkeypatch):
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "0")
    app = create_app("test")
    app.extensions["mail_sender"] = LocalMailSender()

    for n in range(app.config["CONTACT_RATE_LIMIT"]):
        assert _post(app, f"198.51.100.{n}").status_code == 204
    # Every request came from the same connection: a different header is not a different visitor.
    assert _post(app, "198.51.100.200").status_code == 429
