"""The mail seam: what the backend needs to send one message, and nothing else.

Two implementations: `SesMailSender` (the real one) and `LocalMailSender` (a double for tests and local
development, refused in production). Same pattern and same reason as the identity seam: the suite
never depends on AWS. A sender delivers the message or raises `ContactUnavailable`; it never keeps it,
queues it or logs its content.
"""

from abc import ABC, abstractmethod
from email.message import EmailMessage


class MailSender(ABC):
    @abstractmethod
    def send(self, message: EmailMessage) -> None:
        """Deliver to the message's `To`, from its `From`. Raises ContactUnavailable on any failure."""
