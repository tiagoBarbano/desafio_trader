import asyncio, json
from aredis_om import Migrator
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.schema.order_schema import Order, Status, Transacao
from app.service.utils import post_message, post_message_dlq
from app.schema.transacao_schema import Transation
from app.config import RABBIT_MQ
from fastapi import FastAPI


async def findOrderToOrder(app: FastAPI):
    await Migrator().run()
    connection = await connect_robust(RABBIT_MQ)
    app.state.rabbit_connection_to_booking = connection

    # Creating a channel
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=200)
    app.state.rabbit_channel_to_booking = channel

    exchange = await channel.declare_exchange("desafio", ExchangeType.TOPIC)
    app.state.rabbit_exchange = exchange

    queue = await channel.declare_queue("queue.to_booking", durable=True)
    app.state.rabbit_queue_to_booking = queue

    # Binding the queue to the exchange
    await queue.bind(exchange, routing_key='queue.to_booking')

async def consumefindOrderToOrder(app: FastAPI):
    await app.state.rabbit_queue_to_booking.consume(on_findOrderToOrder)
            
async def on_findOrderToOrder(message: IncomingMessage) -> None:
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
                                              
                await post_message(msg, None, "queue.created_booking", "queue.created_booking")
            else:
                await post_message(OrderInput, None, "queue.pending.booking", "queue.pending_booking")    
    except Exception as ex:
        await post_message_dlq(OrderInput, None, "queue.dlq", "queue.dlq")
        OrderMatch[0].statusOrdem = Status.PENDENTE
        OrderInput.statusOrdem = Status.PENDENTE
        await OrderMatch[0].save()
        await OrderInput.save()
        raise Exception(str(ex))
