from services.logging import logging_config_dict

bind = "unix:/tmp/gunicorn-opencodelists.sock"
workers = 2
timeout = 60

# Where to log to (stdout and stderr)
accesslog = "-"
errorlog = "-"

# Configure log structure
# http://docs.gunicorn.org/en/stable/settings.html#logconfig-dict
logconfig_dict = logging_config_dict
