from aredis_om import get_redis_connection, JsonModel, Field
import enum
from datetime import datetime, date
from app.config import HOST_REDIS, PORT_REDIS
from pydantic import BaseModel



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
        
class OrderSchema(BaseModel):
    id: int | None
    myUUID : str
    tipoTransacao: Transacao
    precoMedio: float
    qtdOrdem: int
    idConta: int
    dataOrdem: date
    nomeAtivo: Ativo
    statusOrdem: Status
    valorOrdem: float
    
    class Config:
        orm_mode = True
   