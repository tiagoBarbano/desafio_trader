import json
from aredis_om import Migrator
from aio_pika import connect_robust, IncomingMessage, ExchangeType
from app.schema.order_schema import Order, Status, Transacao, OrderSchema
from app.service.utils import post_message, post_message_dlq
from app.schema.transacao_schema import Transation
from app.config import RABBIT_MQ
from fastapi import FastAPI
from app.repository import get_order_to_booking, save, saveModel
from app.service.contaProxy import contaProxyCredita, contaProxyDebita
from app.service.utils import montaOrder


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
            
            OrderInput = OrderSchema(myUUID = json_request["myUUID"],
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
                    OrderMatch = await get_order_to_booking(OrderInput.idConta, 
                                                            Transacao.VENDA, 
                                                            Status.PENDENTE, 
                                                            OrderInput.valorOrdem)
                    
                    if OrderMatch != []:
                        credita = contaProxyCredita(OrderMatch[0].idConta,
                                                    OrderMatch[0].qtdOrdem,
                                                    OrderMatch[0].valorOrdem,
                                                    OrderMatch[0].nomeAtivo)
                        
                        debita = contaProxyDebita(OrderInput.idConta,
                                                    OrderInput.qtdOrdem,
                                                    OrderInput.valorOrdem,
                                                    OrderInput.nomeAtivo)
                        
                        if credita == True and debita == True:
                            msg = Transation(orderFind=OrderInput,
                                            orderMatch=OrderMatch[0])
                                                
                            await post_message(msg, "Ordens processadas - booking", "queue.created_booking", "queue.created_booking")
                        else:
                            raise Exception("Problema para gerar o booking")
                    else:
                        await post_message(OrderInput, "Ordem ainda pendente", "queue.pending_booking", "queue.pending_booking")    
                    
                case Transacao.VENDA:
                    OrderMatch = await get_order_to_booking(OrderInput.idConta, 
                                                            Transacao.COMPRA, 
                                                            Status.PENDENTE, 
                                                            OrderInput.valorOrdem)
                    
                    if OrderMatch != []:
                        credita = await contaProxyCredita(OrderInput.idConta,
                                                    OrderInput.qtdOrdem,
                                                    OrderInput.valorOrdem,
                                                    OrderInput.nomeAtivo)
                        
                        debita = await contaProxyDebita(OrderMatch[0].idconta,
                                                    OrderMatch[0].qtdordem,
                                                    OrderMatch[0].valorordem,
                                                    OrderMatch[0].nomeativo)
                        
                        if credita == True and debita == True:
                            OrderMatchMQ = montaOrder(OrderMatch[0])

                            OrderInput.statusOrdem = Status.EFETIVADA
                            
                            await save(OrderInput)
                            await save(OrderMatchMQ)
                            
                            msg = Transation(orderFind=OrderInput,
                                            orderMatch=OrderMatchMQ)
                                                
                            await post_message(msg, "Ordens processadas - booking", "queue.created_booking", "queue.created_booking")
                        else:
                            raise Exception("Problema para gerar o booking")
                    else:
                        await post_message(OrderInput, "Ordem ainda pendente", "queue.pending_booking", "queue.pending_booking")                        
                case _:
                    raise Exception("Transacao não identificada")

    except Exception as ex:
        await post_message_dlq(OrderInput, str(ex), "queue.dlq", "queue.dlq")
        OrderMatch[0].statusOrdem = Status.PENDENTE
        OrderInput.statusOrdem = Status.PENDENTE
        await saveModel(OrderMatch[0])
        await save(OrderInput)
        raise Exception(str(ex))
    
