import asyncio, json
from fastapi import HTTPException, status
from aredis_om import Migrator
from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from datetime import datetime
from app.schema.order_schema import Order, Ativo, Status, Transacao
from app.service.utils import post_message, post_message_dlq
from app.service.contaProxy import contaProxy


async def createOrder():
    await Migrator().run()
    connection = await connect_robust("amqp://guest:guest@127.0.0.1/")

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=200)
        queue = await channel.declare_queue("queue.to_create_order", durable=True)
        await queue.consume(on_message)

        print(" [*] Waiting for messages to createOrder. To exit press CTRL+C")
        await asyncio.Future()
            
async def on_message(message: AbstractIncomingMessage) -> None:
    try:
        async with message.process():
            json_request = json.loads(message.body.decode())
            
            newOrder = Order(myUUID = json_request["myUUID"],
                            tipoTransacao = json_request["tipoTransacao"],
                            precoMedio = json_request["precoMedio"],
                            qtdOrdem = json_request["qtdOrdem"],
                            idConta = json_request["idConta"],
                            dataOrdem = datetime.now(),
                            nomeAtivo = Ativo.VIBRANIUM,
                            statusOrdem = Status.PENDENTE,
                            valorOrdem = json_request["precoMedio"] * json_request["qtdOrdem"])
                
            resposta = await contaProxy(newOrder.idConta)
            
            if resposta == 1:
                raise Exception("Problema na Validacao da conta")
            
            match newOrder.tipoTransacao:
                case Transacao.COMPRA:
                    validaSaldoCompra(resposta, newOrder)
                case Transacao.VENDA:            
                    validaSaldoVenda(resposta, newOrder)

            try: 
                await newOrder.save()
            except Exception as ex:
                await post_message_dlq(newOrder, str(ex), "queue.dlq", "queue.dlq")
                raise Exception(str(ex))
            
            try: 
                await post_message(newOrder, None, "queue.created_order", "queue.created_order")
            except Exception as ex:
                await post_message_dlq(newOrder, None, "queue.dlq", "queue.dlq")
                await newOrder.delete()
                raise Exception(str(ex))
    except Exception as ex:
        await post_message_dlq(newOrder, ex, "queue.dlq", "queue.dlq")
        raise Exception(str(ex))
    
    
async def validaSaldoCompra(resposta, newOrder):
    try:
        orderPendings = await Order.find(Order.idConta == newOrder.idConta,
                                Order.tipoTransacao == Transacao.COMPRA,
                                Order.statusOrdem == Status.PENDENTE).all()

        for ordersPending in orderPendings:
            saldoComprometido = ordersPending.valorOrdem + saldoComprometido
        
        saldoReal = resposta.get("SaldoConta") - (saldoComprometido + newOrder.valorOrdem)
        
        if saldoReal > 0:
            await post_message(newOrder,
                            "Saldo Insuficiente para Compra",
                            "queue.recused_order", 
                            "queue.recused_order")
            raise Exception("Saldo Insuficiente para Compra")
    except Exception as ex:
        raise Exception(str(ex))
    
    
async def validaSaldoVenda(resposta, newOrder):
    try:
        orderPendings = await Order.find(Order.idConta == newOrder.idConta,
                                    Order.tipoTransacao == Transacao.VENDA,
                                    Order.statusOrdem == Status.PENDENTE).all()

        for ordersPending in orderPendings:
            saldoComprometido = ordersPending.valorOrdem + saldoComprometido
        
        saldoReal = resposta.get("ValorAtivos") - (newOrder.valorOrdem - saldoComprometido)
        
        if saldoReal < 0:
            await post_message(newOrder,
                            "Saldo Insuficiente para Venda",
                            "queue.recused_order", 
                            "queue.recused_order")
            
            raise Exception("Saldo Insuficiente para Venda")
    except Exception as ex:
         raise Exception(str(ex))