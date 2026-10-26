"""Checking that a notification comes from Mercado Pago: the `x-signature` header, by hand.

As the documentation's "Sin SDKs" steps describe it
(https://www.mercadopago.com.ar/developers/es/docs/your-integrations/notifications/webhooks):

1. `x-signature` looks like `ts=1704908010,v1=618c85...`: split on commas, then on `=`.
2. The manifest is `id:[data.id];request-id:[x-request-id];ts:[ts];`, where `data.id` is the query
   parameter, in lowercase when it is alphanumeric. A part whose value did not arrive is left out.
3. HMAC-SHA256 of the manifest, with the application's secret key, in hexadecimal, must equal `v1`.

The age of `ts` is not checked: the documentation leaves it optional and does not say whether retries,
which go on for days, carry a new one. A replayed notification does no harm: the payment is always read
again from Mercado Pago, and recording it is idempotent.
"""

import hashlib
import hmac


def _parts(header: str) -> dict[str, str]:
    parts = {}
    for piece in header.split(","):
        key, sep, value = piece.partition("=")
        if sep:
            parts[key.strip()] = value.strip()
    return parts


def manifest(*, data_id: str | None, request_id: str | None, ts: str) -> str:
    text = ""
    if data_id:
        text += f"id:{data_id.lower()};"
    if request_id:
        text += f"request-id:{request_id};"
    return text + f"ts:{ts};"


def sign(secret: str, *, data_id: str | None, request_id: str | None, ts: str) -> str:
    message = manifest(data_id=data_id, request_id=request_id, ts=ts)
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def is_valid(secret: str, *, x_signature: str | None, request_id: str | None, data_id: str | None) -> bool:
    if not secret or not x_signature:
        return False
    parts = _parts(x_signature)
    ts, v1 = parts.get("ts"), parts.get("v1")
    if not ts or not v1:
        return False
    expected = sign(secret, data_id=data_id, request_id=request_id, ts=ts)
    return hmac.compare_digest(expected, v1.lower())
