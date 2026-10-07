from app.services.mail.base import MailSender
from app.services.mail.local import LocalMailSender
from app.services.mail.ses import SesMailSender

__all__ = ["LocalMailSender", "MailSender", "SesMailSender", "build_mail_sender"]


def build_mail_sender(config) -> MailSender:
    if config.MAIL_SENDER == "ses":
        return SesMailSender(region=config.SES_REGION, profile=config.AWS_PROFILE)
    return LocalMailSender()
