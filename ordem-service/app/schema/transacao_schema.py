from aredis_om import get_redis_connection, JsonModel
from app.schema.order_schema import Order, OrderSchema
from app.config import HOST_REDIS, PORT_REDIS
from pydantic import BaseModel


redis = get_redis_connection(host=HOST_REDIS, port=PORT_REDIS, decode_responses=True)

class Transation(JsonModel):
    orderFind : Order
    orderMatch: Order
    
    class Meta:
        database = redis
        
class Transation(BaseModel):
    orderFind : OrderSchema
    orderMatch: OrderSchema
            