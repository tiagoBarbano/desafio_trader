import asyncio, json
from datetime import datetime
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.schema.schema import Order, Orquestrador, Evento, Status, save_event
from app.service.utils import post_message
from app.config import RABBIT_MQ, logger
from fastapi import FastAPI


async def pendingBookingQueue(app: FastAPI):
    connection = await connect_robust(RABBIT_MQ)
    app.state.rabbit_connection_pending_booking = connection

    # Creating a channel
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=200)
    app.state.rabbit_channel_pending_booking = channel

    exchange = await channel.declare_exchange("desafio", ExchangeType.TOPIC)
    app.state.rabbit_exchange = exchange

    queue = await channel.declare_queue("queue.pending_booking", durable=True)
    app.state.rabbit_queue_pending_booking = queue

    # Binding the queue to the exchange
    await queue.bind(exchange, routing_key='queue.pending_booking')

async def consumePendingBooking(app: FastAPI):
    await app.state.rabbit_queue_pending_booking.consume(on_pendingBookingQueue)                  

async def on_pendingBookingQueue(message: IncomingMessage) -> None:
    async with message.process():
        logger.info(" [*] Inicio on_pendingBookingQueue")
        request = message.body.decode()
        json_request = json.loads(request)
        uuid = str(message.headers.get("UUID"))
        desc_status = str(message.headers.get("Status"))

        evento = Orquestrador(date = datetime.now(),
                            uuid = uuid,
                            entrada = str(json_request),
                            evento = Evento.BATIMENTO,
                            status = Status.PENDENTE,
                            descricao = desc_status)
        
        await save_event(evento)
        logger.info(" [*] Termino SaveEvent")
