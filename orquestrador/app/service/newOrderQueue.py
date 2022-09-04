import asyncio, json
from datetime import datetime
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.service.utils import post_message
from app.schema.schema import Order, Orquestrador, Evento, Status, save_event
from app.config import RABBIT_MQ, logger
from fastapi import FastAPI


async def newOrderQueue(app: FastAPI):
    connection = await connect_robust(RABBIT_MQ)
    app.state.rabbit_connection_new_order = connection

    # Creating a channel
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=200)
    app.state.rabbit_channel_new_order = channel

    exchange = await channel.declare_exchange("desafio", ExchangeType.TOPIC)
    app.state.rabbit_exchange = exchange

    queue = await channel.declare_queue("queue.new_order", durable=True)
    app.state.rabbit_queue_new_order = queue

    # Binding the queue to the exchange
    await queue.bind(exchange, routing_key='queue.new_order')

async def consumeNewOrder(app: FastAPI):
    await app.state.rabbit_queue_new_order.consume(on_newOrderQueue)
                
async def on_newOrderQueue(message: IncomingMessage) -> None:
    async with message.process():
        logger.info(" [*] Inicio newOrderQueue.")
        request = message.body.decode()
        json_request = json.loads(request)
        headers = str(message.headers.get("UUID"))
        
        newOrder = Order(myUUID = headers,
                        tipoTransacao = json_request["tipoTransacao"],
                        precoMedio = json_request["precoMedio"],
                        qtdOrdem = json_request["qtdOrdem"],
                        idConta = json_request["idConta"])
    
        await post_message(newOrder, "queue.to_create_order", "queue.to_create_order")
        logger.info(" [*] Termino newOrderQueue.")
            
        evento = Orquestrador(date = datetime.now(),
                            uuid = headers,
                            entrada = str(newOrder),
                            evento = Evento.CRIACAO,
                            status = Status.PENDENTE)
        
        await save_event(evento)
        logger.info(" [*] Termino SaveEvent")

        
        
    
        

