from services.logging import logging_config_dict

bind = "0.0.0.0:7000"

workers = 8
timeout = 120

# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

# Configure log structure
# http://docs.gunicorn.org/en/stable/settings.html#logconfig-dict
logconfig_dict = logging_config_dict
