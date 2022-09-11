from typing import Any
from fastapi import FastAPI
from app.service import init_service
from opentelemetry import trace
from opentelemetry.exporter import jaeger
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor, Span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
from app.config import PORT_JAEGER, HOST_JAEGER
from starlette_prometheus import metrics, PrometheusMiddleware
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from app.database import engine


def create_app():
    app: Any = FastAPI(
            title="Ordem SERVICE",
            description="",
            version="1.0.0",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc"
          )
     
    resource = Resource.create(attributes={"service.name": "initOrder"})

    # trace.set_tracer_provider(TracerProvider(resource=resource))
    # tracer = trace.get_tracer(__name__)
    
    # otlp_exporter = OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)
    # span_processor = BatchSpanProcessor(otlp_exporter)
    
    # trace.get_tracer_provider().add_span_processor(span_processor)

    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    tracer.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name=HOST_JAEGER,agent_port=PORT_JAEGER,)))
    
    def server_request_hook(span: Span, scope: dict):
        if span and span.is_recording():
            span.set_attribute("server_request", str(scope))

    def client_request_hook(span: Span, scope: dict):
        if span and span.is_recording():
            span.set_attribute("client_request", str(scope))

    def client_response_hook(span: Span, message: dict):
        if span and span.is_recording():
            span.set_attribute("client_response", str(message))   
    
    FastAPIInstrumentor.instrument_app(app,
                                       server_request_hook=server_request_hook, 
                                       client_request_hook=client_request_hook, 
                                       client_response_hook=client_response_hook) 
    AioPikaInstrumentor().instrument()
    #RedisInstrumentor().instrument(tracer_provider=tracer)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
        
    app.add_middleware(PrometheusMiddleware)
    app.add_route("/metrics", metrics)
    
    app.include_router(init_service.router)
        
    return app
