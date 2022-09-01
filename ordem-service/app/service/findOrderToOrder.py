import asyncio, json
from aredis_om import Migrator
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from app.schema.order_schema import Order, Status, Transacao
from app.service.utils import post_message, post_message_dlq
from app.schema.transacao_schema import Transation


async def findOrderToOrder():
    await Migrator().run()
    connection = await connect_robust("amqp://guest:guest@127.0.0.1/")

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=200)
        queue = await channel.declare_queue("queue.to_booking", durable=True)
        await queue.consume(on_findOrderToOrder)

        print(" [*] Waiting for messages to findOrderToOrder. To exit press CTRL+C")
        await asyncio.Future()
            
async def on_findOrderToOrder(message: AbstractIncomingMessage) -> None:
    try: 
        async with message.process():
            json_request = json.loads(message.body.decode())
            
            OrderInput = Order(myUUID = json_request["myUUID"],
                            tipoTransacao = json_request["tipoTransacao"],
                            precoMedio = json_request["precoMedio"],
                            qtdOrdem = json_request["qtdOrdem"],
                            idConta = json_request["idConta"],
                            dataOrdem = json_request["dataOrdem"],
                            nomeAtivo = json_request["nomeAtivo"],
                            statusOrdem = json_request["statusOrdem"],
                            valorOrdem = json_request["valorOrdem"])
            
            match OrderInput.tipoTransacao:
                case Transacao.COMPRA:
                    OrderMatch = await Order.find(Order.tipoTransacao == Transacao.VENDA,
                                                Order.statusOrdem == Status.PENDENTE,
                                                Order.valorOrdem == OrderInput.valorOrdem).all()
                case Transacao.VENDA:
                    OrderMatch = await Order.find(Order.tipoTransacao == Transacao.COMPRA,
                                                Order.statusOrdem == Status.PENDENTE,
                                                Order.valorOrdem == OrderInput.valorOrdem).all()
                case _:
                    raise Exception("Transacao não identificada")
                
            if OrderMatch != []:
                OrderMatch[0].statusOrdem = Status.PROCESSANDO
                OrderInput.statusOrdem = Status.PROCESSANDO
                await OrderMatch[0].save()
                await OrderInput.save()
                
                msg = Transation(orderFind=OrderInput,
                                 orderMatch=OrderMatch[0])
                               
                #json_string = json.dumps(msg)
                
                
                #envio = msg.encode()
                
                await post_message(msg, None, "queue.created_booking", "queue.created_booking")
                
            await post_message(OrderInput, None, "queue.pending.booking", "queue.pending_booking")    
    except Exception as ex:
        await post_message_dlq(OrderInput, None, "queue.dlq", "queue.dlq")
        OrderMatch[0].statusOrdem = Status.PENDENTE
        OrderInput.statusOrdem = Status.PENDENTE
        await OrderMatch[0].save()
        await OrderInput.save()
        raise Exception(str(ex))
