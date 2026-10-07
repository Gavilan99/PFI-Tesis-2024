"""Capture every log record of every logger, at DEBUG, boto's included, so a leak at any level shows."""

import logging

import pytest


class _Capture(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.lines: list[str] = []

    def emit(self, record):
        text_parts = [record.getMessage(), repr(record.args), repr(record.__dict__)]
        if record.exc_info:
            text_parts.append(logging.Formatter().formatException(record.exc_info))
        self.lines.append(" ".join(text_parts))


@pytest.fixture()
def captured_logs():
    handler = _Capture()
    loggers = [logging.getLogger()] + [
        logging.getLogger(name) for name in list(logging.Logger.manager.loggerDict)
    ]
    previous = [(logger, logger.level) for logger in loggers]
    for logger in loggers:
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    yield handler.lines
    for logger, level in previous:
        logger.removeHandler(handler)
        logger.setLevel(level)
