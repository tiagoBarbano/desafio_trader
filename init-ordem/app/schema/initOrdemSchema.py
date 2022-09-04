from redis_om import get_redis_connection, JsonModel
import enum
from app.config import HOST_REDIS, PORT_REDIS


# This should be a different database
redis = get_redis_connection(host=HOST_REDIS, port=PORT_REDIS, decode_responses=True)

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