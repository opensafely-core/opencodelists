import os

import structlog

# add logging before app has booted
DEBUG = os.getenv("DEBUG", default=False)


def timestamper(logger, log_method, event_dict):
    """
    Add timestamps to logs conditionally

    Structlog provides a Timestamper processor.  However, we only want to
    timestamp logs locally since Production (systemd) stamps logs for us.  This
    mirrors how the Timestamper processor stamps events internally.
    """
    if not DEBUG:
        return event_dict

    # mirror how structlogs own Timestamper calls _make_stamper
    stamper = structlog.processors._make_stamper(fmt="iso", utc=True, key="timestamp")
    return stamper(event_dict)


pre_chain = [
    # Add the log level and a timestamp to the event_dict if the log entry
    # is not from structlog.
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    timestamper,
]

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        timestamper,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging_config_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(colors=DEBUG),
            "foreign_pre_chain": pre_chain,
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "formatter",
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if os.getenv("DJANGO_LOG_DB") else "INFO",
            "propagate": False,
        },
        "gunicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django_structlog": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "builder": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "codelists": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "coding_systems": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "mappings": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "opencodelists": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
