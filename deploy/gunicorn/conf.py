from opentelemetry.instrumentation.django import DjangoInstrumentor
from services.tracing import set_up_tracing, response_hook

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


# Because of Gunicorn's pre-fork web server model,
# we need to initialise opentelemetry in gunicorn's post_fork method
# in order to instrument our application process, see:
# https://opentelemetry-python.readthedocs.io/en/latest/examples/fork-process-model/README.html
def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

    set_up_tracing()

    # Initialise the automatic Django instrumentation
    # https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/django/django.html#id1
    DjangoInstrumentor().instrument(response_hook=response_hook)
