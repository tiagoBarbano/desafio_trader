import uuid
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from redis_om import get_redis_connection, JsonModel
import enum
from aio_pika import connect_robust, Message, RobustConnection, ExchangeType


router = APIRouter()

# This should be a different database
redis = get_redis_connection(host="localhost", port=6379, decode_responses=True)

class Transacao(str, enum.Enum):
    COMPRA = "COMPRA"
    VENDA = "VENDA"

class InitOrder(JsonModel):
    tipoTransacao: Transacao
    precoMedio: float
    qtdOrdem: int
    idConta: int

    class Meta:
        database = redis

@router.post('/orders')
async def create(request: InitOrder, background_tasks: BackgroundTasks):
    try:
        my_uuid = uuid.uuid4()
        queue_name = "queue.new_order"
        routing_key = "queue.new_order"
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust("amqp://guest:guest@127.0.0.1/")
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        await queue.bind(exchange, routing_key)

        await exchange.publish(
            Message(
                bytes(request.json(), 'utf-8'),
                content_type='json/plain',
                headers={'UUID': str(my_uuid)}
            ),
            routing_key
        )
            
        background_tasks.add_task(saveRequest, request)
                    
        return { "message":"Ordem Recebida"}
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))

def saveRequest(request: InitOrder):
    request.save()