"""Functions to configure OTel tracing and instrumentation.

We use OpenTelemetry (OTel) to instrument the app and capture telemetry
data about requests in traces and spans emitted by our code. We send
this data to Honeycomb to view and interrogate it, helping us to
understand the internal state of our system and assist our users.

In production, the functions below are invoked in
deploy/gunicorn/conf.py. OTel requires environment variables to be set;
these are described in dotenv-sample and DEPLOY.md."""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def set_up_tracing():
    """Setup tracing infrastructure for production.

    The resource represents the entity producing telemetry data.
    We configure a global default OTel TracerProvider, because the OTel
    Tracing API should be used to configure and set a TracerProvider
    once, at the start of a process (in prod, this is a gunicorn worker
    process)). TracerProvider provides Tracers and Tracers create Spans.
    https://opentelemetry.io/docs/specs/otel/trace/api/#tracerprovider.
    OTLPSpanExporter sends our telemetry data to Honeycomb. No endpoint
    argument is passed to the exporter, so it uses the value stored
    in OTEL_EXPORTER_OLTP_ENDPOINT environment variable.
    https://opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter.
    We use a BatchSpanProcessor as this is asynchronous, and queues and
    retries sending telemetry data."""

    resource = Resource.create(attributes={"service.name": "opencodelists"})

    trace.set_tracer_provider(TracerProvider(resource=resource))
    span_processor = BatchSpanProcessor(OTLPSpanExporter())
    trace.get_tracer_provider().add_span_processor(span_processor)


def response_hook(span, request, response):
    """Add user data to spans so that we can query this in Honeycomb.

    OTel's request_hook and response_hook run at span creation for a request
    and just before span completion for the response. As request_hook
    runs before authentication middleware has added a 'user' attribute
    to a request, we use a response_hook to access the request after the
    middleware has run so we can include user data in the spans.
    https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/django/django.html#request-and-response-hooks"""
    if hasattr(request, "user"):
        span.set_attribute("user", request.user.username)
