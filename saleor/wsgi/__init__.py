"""WSGI config for saleor project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.
"""
import os
import ast
import jaeger_client
import jaeger_client.config
import opentracing

from uwsgidecorators import postfork
from django.core.wsgi import get_wsgi_application
from django.utils.functional import SimpleLazyObject

from saleor.wsgi.health_check import health_check


def get_allowed_host_lazy():
    from django.conf import settings

    return settings.ALLOWED_HOSTS[0]


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

# This application object is used by any WSGI server configured to use this
# file. This includes Django's development server, if the WSGI_APPLICATION
# setting points here.
application = get_wsgi_application()
# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
application = health_check(application, "/health/")

# Warm-up the django application instead of letting it lazy-load
application(
    {
        "REQUEST_METHOD": "GET",
        "SERVER_NAME": SimpleLazyObject(get_allowed_host_lazy),
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_PORT": 80,
        "PATH_INFO": "/graphql/",
        "wsgi.input": b"",
        "wsgi.multiprocess": True,
    },
    lambda x, y: None,
)

def get_bool_from_env(name, default_value):
    if name in os.environ:
        value = os.environ[name]
        try:
            return ast.literal_eval(value)
        except ValueError as e:
            raise ValueError("{} is an invalid value for {}".format(value, name)) from e
    return default_value


@postfork
def init_jeager_client():
    print('======================================================')
    print('====== Start Init Jeager Client Post Fork Start ======')
    print('======================================================')
    from django.conf import settings
    tracer = settings.INIT_JAEGER_CLIENT("JAEGER_LOGGING", False)
    opentracing.set_global_tracer(tracer)
    # if "JAEGER_AGENT_HOST" in os.environ:
    #     tracer = jaeger_client.Config(
    #         config={
    #             "sampler": {"type": "const", "param": 1},
    #             "local_agent": {
    #                 "reporting_port": os.environ.get(
    #                     "JAEGER_AGENT_PORT", jaeger_client.config.DEFAULT_REPORTING_PORT
    #                 ),
    #                 "reporting_host": os.environ.get("JAEGER_AGENT_HOST"),
    #             },
    #             "logging": get_bool_from_env("JAEGER_LOGGING", False),
    #         },
    #         service_name="saleor",
    #         validate=True,
    #     ).initialize_tracer()
    #     opentracing.set_global_tracer(tracer)
    print('======================================================')
    print('========== Complete Init Jeager Client ===============')
    print('======================================================')
    with tracer.start_active_span('Saleor.ForkProcess') as scope:
        span = scope.span
        span.set_tag("python_file", "wsgi/__init__.py")
        span.set_tag("jaeger_port", os.environ.get(
                        "JAEGER_AGENT_PORT", jaeger_client.config.DEFAULT_REPORTING_PORT
                    ))
        span.set_tag("jaeger_host", os.environ.get("JAEGER_AGENT_HOST"))
        span.set_tag("jaeger_logging", get_bool_from_env("JAEGER_LOGGING", False))
        import time
        time.sleep(5)
        span.finish()
    print('======================================================')
    print('============= End Init Jeager Client =================')
    print('======================================================')
    print('======================================================')
    print('========== End Init Jeager Client Post Fork End ======')
    print('======================================================')
