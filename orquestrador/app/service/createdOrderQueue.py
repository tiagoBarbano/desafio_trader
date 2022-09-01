import asyncio, json
from datetime import datetime
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from app.schema.schema import Order, Orquestrador, Evento, Status, save_event
from app.service.utils import post_message


async def createdOrderQueue():
    connection = await connect_robust("amqp://guest:guest@127.0.0.1/")    
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=200)
        queue = await channel.declare_queue("queue.created_order", durable=True)
        await queue.consume(on_createdOrderQueue)

        print(" [*] Waiting for messages to createdOrderQueue. To exit press CTRL+C")
        await asyncio.Future()        

async def on_createdOrderQueue(message: AbstractIncomingMessage) -> None:
    async with message.process():
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
        
        evento = Orquestrador(date = datetime.now(),
                            uuid = uuid,
                            entrada = str(json_request),
                            evento = Evento.CRIACAO,
                            status = Status.EFETIVADA)
        
        await save_event(evento)
