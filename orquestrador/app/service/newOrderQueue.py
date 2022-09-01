import asyncio, json
from datetime import datetime
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from app.service.utils import post_message
from app.schema.schema import Order, Orquestrador, Evento, Status, save_event



async def newOrderQueue():
    connection = await connect_robust("amqp://guest:guest@127.0.0.1/")
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=200)
        queue = await channel.declare_queue("queue.new_order", durable=True)
        await queue.consume(on_newOrderQueue)

        print(" [*] Waiting for messages to newOrderQueue. To exit press CTRL+C")
        await asyncio.Future()
                
async def on_newOrderQueue(message: AbstractIncomingMessage) -> None:
    async with message.process():
        request = message.body.decode()
        json_request = json.loads(request)
        headers = str(message.headers.get("UUID"))
        
        newOrder = Order(myUUID = headers,
                        tipoTransacao = json_request["tipoTransacao"],
                        precoMedio = json_request["precoMedio"],
                        qtdOrdem = json_request["qtdOrdem"],
                        idConta = json_request["idConta"])
    
        await post_message(newOrder, "queue.to_create_order", "queue.to_create_order")
    
        evento = Orquestrador(date = datetime.now(),
                            uuid = headers,
                            entrada = str(newOrder),
                            evento = Evento.CRIACAO,
                            status = Status.PENDENTE)
        
        await save_event(evento)
        

        
        
    
        

