"""The contact form (/contacto): mailed to our inbox, never stored (decided 05-10).

No table, no file, and no part of the message in the logs: it is personal data of someone who may
not have an account. If sending fails, the person sees the error and sends it again; nothing is
queued.

What the client sends reaches the mail in two places only: the body, and the `Reply-To` and
`Subject` headers. Header values are reduced to one line first, so a crafted name cannot add headers.
"""

import re
from email.message import EmailMessage
from email.policy import SMTP
from email.utils import formataddr

from app.exceptions import ContactRateLimited
from app.services.mail import MailSender
from app.services.rate_limit import SlidingWindowLimiter

SUBJECT_PREFIX = "Contacto NureonAI"
_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")


def single_line(text: str) -> str:
    """Control characters (CR and LF among them) become a space; runs of whitespace collapse."""
    return " ".join(_CONTROL.sub(" ", text).split())


def build_contact_mail(*, name: str, email: str, message: str, mail_to: str, mail_from: str) -> EmailMessage:
    name, email = single_line(name), single_line(email)
    mail = EmailMessage(policy=SMTP)
    mail["From"] = formataddr(("NureonAI contacto", mail_from))
    mail["To"] = mail_to
    mail["Reply-To"] = formataddr((name, email))
    mail["Subject"] = f"{SUBJECT_PREFIX}: {name}"
    mail.set_content(
        "Mensaje enviado desde el formulario de contacto de NureonAI.\n"
        "Respondé este mail para contestarle a quien lo escribió.\n\n"
        f"Nombre: {name}\n"
        f"Email: {email}\n\n"
        f"{message}\n"
    )
    return mail


def send_contact_message(
    sender: MailSender,
    limiter: SlidingWindowLimiter,
    *,
    origin: str,
    name: str,
    email: str,
    message: str,
    mail_to: str,
    mail_from: str,
) -> None:
    if not limiter.allow(origin):
        raise ContactRateLimited()
    sender.send(build_contact_mail(name=name, email=email, message=message, mail_to=mail_to, mail_from=mail_from))
