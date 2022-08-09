import asyncio, enum, json, aiohttp
from fastapi import APIRouter,  HTTPException, status, BackgroundTasks
from aredis_om import get_redis_connection, JsonModel, Migrator, Field
from aio_pika import connect_robust, RobustConnection, ExchangeType, Message
from aio_pika.abc import AbstractIncomingMessage
from datetime import datetime
from opentelemetry.instrumentation.aiohttp_client import create_trace_config


router = APIRouter()
redis = get_redis_connection(host="localhost", port=6379, decode_responses=True)

class Ativo(str, enum.Enum):
    VIBRANIUM = "VIBRANIUM"

class Transacao(str, enum.Enum):
    COMPRA = "COMPRA"
    VENDA = "VENDA"
    
class Status(str, enum.Enum):
    EFETIVADA = "EFETIVADA"
    PROCESSANDO = "PROCESSANDO"
    CANCELADA = "CANCELADA"
    PENDENTE = "PENDENTE"

class Order(JsonModel):
    myUUID : str = Field(index=True)
    tipoTransacao: Transacao = Field(index=True)
    precoMedio: float
    qtdOrdem: int
    idConta: int = Field(index=True)
    dataOrdem: datetime = Field(index=True)
    nomeAtivo: Ativo = Field(index=True)
    statusOrdem: Status = Field(index=True)
    valorOrdem: float
    
    class Meta:
        database = redis


async def createOrder():
    await Migrator().run()
    connection = await connect_robust("amqp://guest:guest@127.0.0.1/")

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue("queue.to_create_order", durable=True)
        await queue.consume(on_message)

        print(" [*] Waiting for messages to createOrder. To exit press CTRL+C")
        await asyncio.Future()
        
        
async def on_message(message: AbstractIncomingMessage) -> None:
    async with message.process():
        request = message.body.decode()
        json_request = json.loads(request)
        
        newOrder = Order(myUUID = json_request["myUUID"],
                        tipoTransacao = json_request["tipoTransacao"],
                        precoMedio = json_request["precoMedio"],
                        qtdOrdem = json_request["qtdOrdem"],
                        idConta = json_request["idConta"],
                        dataOrdem = datetime.now(),
                        nomeAtivo = Ativo.VIBRANIUM,
                        statusOrdem = Status.PENDENTE,
                        valorOrdem = json_request["precoMedio"] * json_request["qtdOrdem"])
        
        params = {'id' : newOrder.idConta }
        
        async with aiohttp.ClientSession(trace_configs=[create_trace_config()]) as session:
            async with session.get("http://localhost:8003/", params=params, ssl=False) as response:
                resposta = await response.json()

        orderPendents = await Order.find(Order.idConta == newOrder.idConta,
                                        Order.tipoTransacao == newOrder.tipoTransacao,
                                        Order.statusOrdem == Status.PENDENTE).all()
        
        if newOrder.tipoTransacao == Transacao.COMPRA:
            print("Regras de Compra")
            
        if newOrder.tipoTransacao == Transacao.VENDA:            
            print("Regras de Venda")
        
                
        try: 
            await newOrder.save()
        except Exception as ex:
            await post_message_dlq(newOrder, "queue.dlq", "queue.dlq")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
        
        try: 
            await post_message(newOrder, "queue.created_order", "queue.created_order")
        except Exception as ex:
            await post_message_dlq(newOrder, "queue.dlq", "queue.dlq")
            await newOrder.delete()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
   

async def post_message(msg, queue_name: str, routing_key: str):
    try:
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust("amqp://guest:guest@127.0.0.1/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(exchange, routing_key)

        await exchange.publish(Message(bytes(msg.json(), 'utf-8'),
                                             content_type='json/plain',
                                             headers={'UUID': str(msg.myUUID)}), routing_key)
           
        print(msg)
    except Exception as ex:
        await post_message_dlq(msg.json(), "queue.dlq", "queue.dlq")
        await delete_order_dlq(msg.json())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    
async def post_message_dlq(msg, queue_name: str, routing_key: str):
    try:
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust("amqp://guest:guest@127.0.0.1/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(exchange, routing_key)

        await exchange.publish(Message(bytes(msg.json(), 'utf-8'),
                                             content_type='json/plain',
                                             headers={'UUID': str(msg.myUUID),
                                                      'evento': 'CRIACAO'}), routing_key)
           
        print(msg)
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))          
    
async def delete_order_dlq(msg) -> None:
    json_request = msg.json()
    await delete_order(json_request["pk"])
        
async def delete_order(request: str):
    await request.delete(request)

async def save_event(request: Order):
    request.save        