"""Amazon SES (API v2), reached with boto3. One call: SendEmail with the raw MIME message.

The envelope is taken from the message's own `From` and `To`, which the backend sets from config: no
address the client sends ends up in it. With raw content, SES authorizes the call as
`ses:SendRawEmail`, not only `ses:SendEmail`: the policy allows both on the `From` identity
(docs/aws-setup.md). In the sandbox, `From` and `To` must both be verified identities; `Reply-To` need
not be.
"""

import logging
from email.message import EmailMessage
from email.utils import parseaddr

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.exceptions import ContactUnavailable
from app.services.mail.base import MailSender

logger = logging.getLogger(__name__)


def _error_code(exc: Exception) -> str:
    if isinstance(exc, ClientError):
        return exc.response.get("Error", {}).get("Code", "")
    return type(exc).__name__


class SesMailSender(MailSender):
    def __init__(self, region: str, *, profile: str | None, client=None):
        if client is None:
            # Explicit profile from config, never boto3's implicit choice. `None` only where config
            # allows it (deployed, with role credentials and no profile file).
            if profile == "default":
                raise ValueError("The 'default' AWS profile is never used by this backend.")
            client = boto3.Session(profile_name=profile, region_name=region).client("sesv2")
        self._client = client

    def send(self, message: EmailMessage) -> None:
        try:
            self._client.send_email(
                FromEmailAddress=parseaddr(message["From"])[1],
                Destination={"ToAddresses": [parseaddr(message["To"])[1]]},
                Content={"Raw": {"Data": message.as_bytes()}},
            )
        except (ClientError, BotoCoreError) as exc:
            # The error code only: SES messages can quote addresses back.
            logger.error("SES SendEmail failed: %s", _error_code(exc))
            raise ContactUnavailable() from None
