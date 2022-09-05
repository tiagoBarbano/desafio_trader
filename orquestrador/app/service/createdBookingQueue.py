import asyncio, json
from datetime import datetime
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.schema.schema import Transation, Orquestrador, Evento, Status, save_event
from app.service.utils import post_message
from app.config import RABBIT_MQ, logger
from fastapi import FastAPI



async def createdBookingQueue(app: FastAPI):
    connection = await connect_robust(RABBIT_MQ)
    app.state.rabbit_connection_created_booking = connection

    # Creating a channel
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=200)
    app.state.rabbit_channel_created_booking = channel

    exchange = await channel.declare_exchange("desafio", ExchangeType.TOPIC)
    app.state.rabbit_exchange = exchange

    queue = await channel.declare_queue("queue.created_booking", durable=True)
    app.state.rabbit_queue_created_booking = queue

    # Binding the queue to the exchange
    await queue.bind(exchange, routing_key='queue.created_booking')

async def consumeCreatedBooking(app: FastAPI):
    await app.state.rabbit_queue_created_booking.consume(on_createdBookingQueue)                  

async def on_createdBookingQueue(message: IncomingMessage) -> None:
    async with message.process():
        logger.info(" [*] Inicio on_createdBookingQueue")
        request = message.body.decode()
        json_request = json.loads(request)
        orderFind = json_request.get("orderFind")
        orderMatch = json_request.get("orderMatch")
        desc_status = str(message.headers.get("Status"))
        
        msg = Transation(orderFind=orderFind,
                         orderMatch=orderMatch)
        
        await post_message(msg, "queue.to_transaction", "queue.to_transaction")
        logger.info(" [*] Termino createdOrderQueue") 

        evento_Order_Find = Orquestrador(date = datetime.now(),
                                        uuid = orderFind.get("myUUID"),
                                        entrada = str(json_request),
                                        evento = Evento.BATIMENTO,
                                        status = Status.EFETIVADA,
                                        descricao = desc_status)
        
        evento_Order_Match = Orquestrador(date = datetime.now(),
                                        uuid = orderMatch.get("myUUID"),
                                        entrada = str(json_request),
                                        evento = Evento.BATIMENTO,
                                        status = Status.EFETIVADA,
                                        descricao = desc_status)
        
        await save_event(evento_Order_Find)
        await save_event(evento_Order_Match)
        logger.info(" [*] Termino SaveEvent")
