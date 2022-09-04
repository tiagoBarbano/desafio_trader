import asyncio, json
from datetime import datetime
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.schema.schema import Order, Orquestrador, Evento, Status, save_event
from app.service.utils import post_message
from app.config import RABBIT_MQ, logger
from fastapi import FastAPI


async def createdOrderQueue(app: FastAPI):
    connection = await connect_robust(RABBIT_MQ)
    app.state.rabbit_connection_created_order = connection

    # Creating a channel
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=200)
    app.state.rabbit_channel_created_order = channel

    exchange = await channel.declare_exchange("desafio", ExchangeType.TOPIC)
    app.state.rabbit_exchange = exchange

    queue = await channel.declare_queue("queue.created_order", durable=True)
    app.state.rabbit_queue_created_order = queue

    # Binding the queue to the exchange
    await queue.bind(exchange, routing_key='queue.created_order')

async def consumeCreatedOrder(app: FastAPI):
    await app.state.rabbit_queue_created_order.consume(on_createdOrderQueue)                  

async def on_createdOrderQueue(message: IncomingMessage) -> None:
    async with message.process():
        logger.info(" [*] Inicio createdOrderQueue")
        request = message.body.decode()
        json_request = json.loads(request)
        uuid = str(message.headers.get("UUID"))
        evento = str(message.headers.get("evento"))
                
        createdOrder = Order(myUUID = json_request["myUUID"],
                        tipoTransacao = json_request["tipoTransacao"],
                        precoMedio = json_request["precoMedio"],
                        qtdOrdem = json_request["qtdOrdem"],
                        idConta = json_request["idConta"],
                        dataOrdem = json_request["dataOrdem"],
                        nomeAtivo = json_request["nomeAtivo"],
                        statusOrdem = json_request["statusOrdem"],
                        valorOrdem = json_request["valorOrdem"])
        
        await post_message(createdOrder, "queue.to_booking", "queue.to_booking")
        logger.info(" [*] Termino createdOrderQueue") 
        
        evento = Orquestrador(date = datetime.now(),
                            uuid = uuid,
                            entrada = str(json_request),
                            evento = Evento.CRIACAO,
                            status = Status.EFETIVADA)
        
        await save_event(evento)
        logger.info(" [*] Termino SaveEvent")
