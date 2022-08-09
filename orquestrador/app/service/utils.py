from fastapi import HTTPException, status
from aio_pika import connect_robust, RobustConnection, ExchangeType, Message
import asyncio, json
from datetime import datetime
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from app.schema.schema import Orquestrador, Evento, Status, save_event


async def post_message(msg, queue_name: str, routing_key: str):
    try:
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust("amqp://guest:guest@127.0.0.1/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(exchange, routing_key)

        await exchange.publish(Message(bytes(msg.json(), 'utf-8'), content_type='json/plain'), routing_key)
           
        print(msg)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    

async def consumerDQLQueue():
    connection = await connect_robust("amqp://guest:guest@127.0.0.1/")    
    async with connection:
        # Creating a channel
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)

        # Declaring queue
        queue = await channel.declare_queue("queue.dlq", durable=True)

        # Start listening the queue with name 'task_queue'
        await queue.consume(on_consumerDQLQueue)

        print(" [*] Waiting for messages. To exit press CTRL+C")
        await asyncio.Future()        

async def on_consumerDQLQueue(message: AbstractIncomingMessage) -> None:
    async with message.process():
        request = message.body.decode()
        json_request = json.loads(request)
        headers = str(message.headers.get("UUID"))
        
        evento = Orquestrador(date = datetime.now(),
                            uuid = headers,
                            entrada = str(json_request),
                            evento = Evento.ERRO,
                            status = Status.CANCELADA)
                
        await save_event(evento)