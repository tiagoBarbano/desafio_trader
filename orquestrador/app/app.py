from typing import Any
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from starlette_prometheus import metrics, PrometheusMiddleware
import asyncio
from app.service.createdOrderQueue import createdOrderQueue, consumeCreatedOrder
from app.service.newOrderQueue import newOrderQueue, consumeNewOrder
from app.service.pendingBookingQueue import pendingBookingQueue, consumePendingBooking
from app.service.createdBookingQueue import createdBookingQueue, consumeCreatedBooking
from opentelemetry.instrumentation.redis import RedisInstrumentor
from app.schema import schema
from app.service.utils import consumerDQLQueue, consumeDLQ
from app.config import HOST_JAEGER, PORT_JAEGER


def create_app():
    app: Any = FastAPI(
            title="Orquestrador SERVICE",
            description="",
            version="1.0.0",
            openapi_url="/openapi.json",
            docs_url="/docs",
            redoc_url="/redoc"
          )
       
    resource = Resource.create(attributes={"service.name": "Orquestrador"})
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)
    
    tracer.add_span_processor(BatchSpanProcessor(JaegerExporter(agent_host_name=HOST_JAEGER,agent_port=PORT_JAEGER,)))

    RedisInstrumentor().instrument() 
    AioPikaInstrumentor().instrument()
    FastAPIInstrumentor().instrument_app(app)

    app.add_middleware(PrometheusMiddleware)

    async def start_create():
        await newOrderQueue(app)
        await createdOrderQueue(app)
        await consumerDQLQueue(app)
        await pendingBookingQueue(app)
        await createdBookingQueue(app)        
        
        asyncio.create_task(consumeNewOrder(app))
        asyncio.create_task(consumeCreatedOrder(app))
        asyncio.create_task(consumeDLQ(app))
        asyncio.create_task(consumePendingBooking(app))
        asyncio.create_task(consumeCreatedBooking(app))
        
        print('Listening on queue default')
    
    app.add_route("/metrics", metrics)
    app.include_router(schema.router)    
    app.add_event_handler("startup", start_create)

    return app
