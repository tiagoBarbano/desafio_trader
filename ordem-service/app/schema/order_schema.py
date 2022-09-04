from aredis_om import get_redis_connection, JsonModel, Field
import enum
from datetime import datetime
from app.config import HOST_REDIS, PORT_REDIS


redis = get_redis_connection(host=HOST_REDIS, port=PORT_REDIS, decode_responses=True)

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
    precoMedio: float = Field(index=True)
    qtdOrdem: int = Field(index=True)
    idConta: int = Field(index=True)
    dataOrdem: datetime = Field(index=True)
    nomeAtivo: Ativo = Field(index=True)
    statusOrdem: Status = Field(index=True)
    valorOrdem: float = Field(index=True)
    
    class Meta:
        database = redis