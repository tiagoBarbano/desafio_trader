from typing import Any
from fastapi import FastAPI
from app.service import orquestrador
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def create_app():
    app: Any = FastAPI(
            title="Ordem SERVICE",
            description="",
            version="1.0.0",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc"
          )
       
    resource = Resource.create(attributes={"service.name": "Orquestrador"})
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    tracer.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name="localhost",agent_port=6831,)))

    FastAPIInstrumentor().instrument_app(app)
    AioPikaInstrumentor().instrument()
    RedisInstrumentor().instrument() 
  
    async def start_create():
        await orquestrador.init_Orquestrador()
        
    app.add_event_handler("startup",start_create)

    return app
