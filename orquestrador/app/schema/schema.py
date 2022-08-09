import enum
from aredis_om import get_redis_connection, JsonModel, Migrator
from datetime import datetime


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
    
class Evento(str, enum.Enum):
    CRIACAO = "CRIACAO"
    VALIDACAO_SALDO = "VALIDACAO_SALDO"
    BATIMENTO = "BATIMENTO"
    EFETIVACAO = "EFETIVACAO"
    CANCELAMENTO = "CANCELAMENTO"
    ERRO = "ERRO"

class Orquestrador(JsonModel):
    date: datetime
    uuid: str
    entrada: str
    evento: Evento
    status: Status

    class Meta:
        database = redis

class Order(JsonModel):
    myUUID = str
    tipoTransacao: Transacao
    precoMedio: float
    qtdOrdem: int
    idConta: int
    
    class Meta:
        database = redis        
        
async def save_event(evento: Orquestrador):
    await Migrator().run()
    await evento.save()