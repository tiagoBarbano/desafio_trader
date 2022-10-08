from fastapi import HTTPException, status
from aio_pika import connect_robust, RobustConnection, ExchangeType, Message, IncomingMessage, ExchangeType
import asyncio, json
from datetime import datetime
from aio_pika import connect_robust
from app.schema.schema import Orquestrador, Evento, Status, save_event
from app.config import RABBIT_MQ
from fastapi import FastAPI



async def post_message(msg, queue_name: str, routing_key: str):
    try:
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust(RABBIT_MQ)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(exchange, routing_key)

        await exchange.publish(Message(bytes(msg.json(), 'utf-8'), content_type='json/plain'), routing_key)
           
        print(msg)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    

async def consumerDQLQueue(app: FastAPI):
    connection = await connect_robust(RABBIT_MQ)
    app.state.rabbit_connection_dlq = connection

    # Creating a channel
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=200)
    app.state.rabbit_channel_dlq = channel

    exchange = await channel.declare_exchange("desafio", ExchangeType.TOPIC)
    app.state.rabbit_exchange = exchange

    queue = await channel.declare_queue("queue.dlq", durable=True)
    app.state.rabbit_queue_dlq = queue

    # Binding the queue to the exchange
    await queue.bind(exchange, routing_key='queue.dlq')

async def consumeDLQ(app: FastAPI):
    await app.state.rabbit_queue_dlq.consume(on_consumerDQLQueue)           

async def on_consumerDQLQueue(message: IncomingMessage) -> None:
    async with message.process():
        request = message.body.decode()
        json_request = json.loads(request)
        headers = str(message.headers.get("UUID"))
        desc = str(message.headers.get("Exception"))        
        
        evento = Orquestrador(date = datetime.now(),
                            uuid = headers,
                            entrada = str(json_request),
                            evento = Evento.ERRO,
                            status = Status.CANCELADA,
                            desc_status = desc)
                
        await save_event(evento)