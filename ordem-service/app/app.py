from typing import Any
from fastapi import FastAPI
from app.service import ordem_service
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor, Span
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor


def create_app():
    app: Any = FastAPI(
            title="Ordem SERVICE",
            description="",
            version="1.0.0",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc"
          )

    resource = Resource.create(attributes={"service.name": "OrdemService"})

    # set the tracer provider
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    
    tracer.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name="localhost",agent_port=6831,)))
    
    def server_request_hook(span: Span, scope: dict):
        if span and span.is_recording():
            span.set_attribute("custom_user_attribute_from_request_hook", "some-value")

    def client_request_hook(span: Span, scope: dict):
        if span and span.is_recording():
            span.set_attribute("custom_user_attribute_from_client_request_hook", "some-value")

    def client_response_hook(span: Span, message: dict):
        if span and span.is_recording():
            span.set_attribute("custom_user_attribute_from_response_hook", "some-value")   
    
    FastAPIInstrumentor.instrument_app(app,
                                       server_request_hook=server_request_hook, 
                                       client_request_hook=client_request_hook, 
                                       client_response_hook=client_response_hook)  

    # Instrument redis
    RedisInstrumentor().instrument()
    AioPikaInstrumentor().instrument()
    #AioHttpClientInstrumentor().instrument()
    
    @app.on_event("startup")
    async def start_create():
        await ordem_service.createOrder()
    return app
