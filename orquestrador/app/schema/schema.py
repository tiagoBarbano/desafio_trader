import enum
from aredis_om import get_redis_connection, JsonModel, Migrator, Field
from datetime import datetime
from fastapi import APIRouter
from app.config import HOST_REDIS, PORT_REDIS
from opentelemetry.instrumentation.redis import RedisInstrumentor


router = APIRouter()

redis = get_redis_connection(host=HOST_REDIS, port=PORT_REDIS, decode_responses=True)

RedisInstrumentor().instrument()

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
    
class Evento(str, enum.Enum):
    CRIACAO = "CRIACAO"
    VALIDACAO_SALDO = "VALIDACAO_SALDO"
    BATIMENTO = "BATIMENTO"
    EFETIVACAO = "EFETIVACAO"
    CANCELAMENTO = "CANCELAMENTO"
    ERRO = "ERRO"

class Orquestrador(JsonModel):
    date: datetime = Field(index=True)
    uuid: str = Field(index=True)
    entrada: str
    evento: Evento = Field(index=True)
    status: Status = Field(index=True)
    desc_status: str | None

    class Meta:
        database = redis

class Order(JsonModel):
    id: int | None
    myUUID: str
    tipoTransacao: Transacao
    precoMedio: float
    qtdOrdem: int
    idConta: int
    
    class Meta:
        database = redis

class Transation(JsonModel):
    orderFind : Order
    orderMatch: Order
    
    class Meta:
        database = redis         
        
async def save_event(evento: Orquestrador):
    await Migrator().run()
    await evento.save()

@router.get("/")    
async def get_event(uuid: str):
    await Migrator().run()
    return await Orquestrador.find(Orquestrador.uuid == uuid).all()