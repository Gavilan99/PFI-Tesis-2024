"""In-memory mail sender, for tests and local development only. Nothing leaves the process.

Not a production mode: config refuses `MAIL_SENDER=local` with `APP_ENV=production`. It holds the last
few messages so tests can read what would have been sent; a restart forgets them.
"""

import logging
import threading
from collections import deque
from email.message import EmailMessage

from app.services.mail.base import MailSender

logger = logging.getLogger(__name__)


class LocalMailSender(MailSender):
    def __init__(self, keep: int = 20):
        self._sent: deque[EmailMessage] = deque(maxlen=keep)
        self._lock = threading.Lock()

    def send(self, message: EmailMessage) -> None:
        with self._lock:
            self._sent.append(message)
        # That it happened, never what it says.
        logger.info("Contact mail kept by the local sender, not sent (MAIL_SENDER=local)")

    @property
    def sent(self) -> list[EmailMessage]:
        with self._lock:
            return list(self._sent)
