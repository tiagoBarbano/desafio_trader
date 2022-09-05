from fastapi import HTTPException, status
from aio_pika import connect_robust, RobustConnection, ExchangeType, Message
from app.schema.order_schema import Order
from app.config import RABBIT_MQ


async def post_message(msg, dsc: str, queue_name: str, routing_key: str):
    try:
        uuid: str = ""
        if(hasattr(msg, 'myUUID')):
            uuid = msg.myUUID
        else:
            uuid = msg.pk        
        exchange = "desafio"
    
        connection: RobustConnection = await connect_robust(RABBIT_MQ)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(exchange, routing_key)
              
        await exchange.publish(Message(bytes(msg.json(), 'utf-8'),
                                             content_type='json/plain',
                                             headers={'UUID': str(uuid),
                                                      'Status': str(dsc)}), routing_key)
           
        print(msg)
    except Exception as ex:
        await post_message_dlq(msg.json(), str(ex),"queue.dlq", "queue.dlq")
        await delete_order_dlq(msg.json())
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ex))
    
async def post_message_dlq(msg, dsc: str, queue_name: str, routing_key: str):
    try:
        uuid: str = ""
        if(hasattr(msg, 'myUUID')):
            uuid = msg.myUUID
        else:
            uuid = msg.pk        
 
 
        exchange = "desafio"

        connection: RobustConnection = await connect_robust(RABBIT_MQ)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(exchange, ExchangeType.TOPIC,  )
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await queue.bind(exchange, routing_key)
    
        await exchange.publish(Message(bytes(msg.json(), 'utf-8'),
                                             content_type='json/plain',
                                             headers={'UUID': str(uuid),
                                                      'Event': 'CRIACAO',
                                                      'Exception': str(dsc)}), routing_key)
           
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
