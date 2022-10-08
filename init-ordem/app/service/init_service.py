import uuid
from fastapi import APIRouter, HTTPException, status, Response, BackgroundTasks
from aio_pika import connect_robust, Message, RobustConnection, ExchangeType
#from app.schema.initOrdemSchema import InitOrder
from app.schema.initOrdemSchemaPG import OrderSchema
from app.model import OrderModel
from app.repository import saveInitOrder
from app.config import RABBIT_MQ, logger


router = APIRouter()

@router.post('/orders', status_code=status.HTTP_201_CREATED)
async def create(request: OrderSchema, background_tasks: BackgroundTasks, response: Response):
    try:
        logger.info("Inicio")
        my_uuid = uuid.uuid4()
        
        orderModel = OrderModel(tipotransacao=str(request.tipoTransacao.COMPRA.capitalize()),
                                precomedio=request.precoMedio,
                                qtdordem=request.qtdOrdem,
                                idconta=request.idConta,
                                myuuid=str(my_uuid))
    
        #background_tasks.add_task(saveInitOrder, orderModel)
                
        queue_name = "queue.new_order"
        routing_key = "queue.new_order"
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust(RABBIT_MQ)
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

        logger.info("Término")            
        response.headers["UUID"] = str(my_uuid)
        return { "message": "Ordem Criada", "uuid": str(my_uuid), "request": str(request)}
    except Exception as ex:
        logger.error("Erro: " + str(ex))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))