from aredis_om import get_redis_connection, JsonModel
from app.schema.order_schema import Order



redis = get_redis_connection(host="localhost", port=6379, decode_responses=True)

class Transation(JsonModel):
    orderFind : Order
    orderMatch: Order
    
    class Meta:
        database = redis