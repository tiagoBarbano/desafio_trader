from typing import Any
from fastapi import FastAPI
from app.service import conta_service
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor, Span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from starlette_prometheus import metrics, PrometheusMiddleware
#from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from app.config import HOST_JAEGER, PORT_JAEGER


def create_app():
    app: Any = FastAPI(
            title="conta SERVICE",
            description="",
            version="1.0.0",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc"
          )
     
    resource = Resource.create(attributes={"service.name": "conta-service"})

    # set the tracer provider
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    
    tracer.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name=HOST_JAEGER,
                                                                agent_port=PORT_JAEGER,)))
        
    def server_request_hook(span: Span, scope: dict):
        if span and span.is_recording():
            span.set_attribute("request", str(scope))

    def client_request_hook(span: Span, scope: dict):
        if span and span.is_recording():
            span.set_attribute("request", str(scope))

    def client_response_hook(span: Span, message: dict):
        if span and span.is_recording():
            span.set_attribute("response", str(message))   
    
    FastAPIInstrumentor.instrument_app(app,
                                       server_request_hook=server_request_hook, 
                                       client_request_hook=client_request_hook, 
                                       client_response_hook=client_response_hook)  

    app.add_middleware(PrometheusMiddleware)
    app.add_route("/metrics", metrics)
    app.include_router(conta_service.router)
        
    return app
