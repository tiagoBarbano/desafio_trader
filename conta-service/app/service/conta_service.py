from fastapi import APIRouter, HTTPException
from aredis_om import get_redis_connection, JsonModel, Field, Migrator
from redis_om import NotFoundError
from app.config import HOST_REDIS, PORT_REDIS, logger
from opentelemetry.instrumentation.redis import RedisInstrumentor



router = APIRouter()

# Instrument redis
RedisInstrumentor().instrument()

redis = get_redis_connection(host=HOST_REDIS, port=PORT_REDIS, decode_responses=True, db=0)

class Conta(JsonModel):
    idConta: int = Field(index=True)
    saldoConta: float = Field(index=True)
    qtdAtivos: int = Field(index=True)
    valorAtivos: float = Field(index=True)
    precoMedio: float = Field(index=True)
    nomeAtivo: str = Field(index=True)

    class Meta:
        database = redis

@router.get("/contas")
async def get_contas():
    contas = await Conta.all_pks()
    return contas

@router.get("/")
async def get_conta_by_id(id: int):
    await Migrator().run()
    try:
        logger.info("Inicio consulta Saldo - conta")
        conta = await Conta.find(Conta.idConta == id).first()
        logger.info("Término consulta Saldo - conta")
        return { "SaldoConta": conta.saldoConta, 
                  "ValorAtivos": conta.valorAtivos } 
    except NotFoundError as ex:
        logger.error("Problema na consulta por ID")
        return "Bad request", 400 

@router.get("/pk/{pk}")
async def get_conta_by_pk(pk: str):
    conta = await Conta.get(pk)
    return conta

@router.post('/')
async def create(request: Conta):
    await request.save()
    return  request

@router.post('/credita-conta')
async def creditaConta(idConta: int, qtdAtivos: int, valorAtivos: float, nomeAtivo: str):
    conta = await Conta.find(Conta.idConta == idConta).first()
    conta.qtdAtivos = conta.qtdAtivos + qtdAtivos
    conta.nomeAtivo = nomeAtivo
    conta.valorAtivos = conta.valorAtivos + valorAtivos
    conta.saldoConta = conta.saldoConta - valorAtivos
    conta.precoMedio = conta.valorAtivos / conta.qtdAtivos
    
    await conta.save()
    
    return  { "message": "Conta Atualizada" }   


@router.post('/debita-conta')
async def debitaConta(idConta: int, qtdAtivos: int, valorAtivos: float, nomeAtivo: str):
    conta = await Conta.find(Conta.idConta == idConta).first()
    conta.qtdAtivos = conta.qtdAtivos - qtdAtivos
    conta.nomeAtivo = nomeAtivo
    conta.valorAtivos = conta.valorAtivos - valorAtivos
    conta.saldoConta = conta.saldoConta + valorAtivos
    conta.precoMedio = conta.valorAtivos / conta.qtdAtivos
    
    await conta.save()
    
    return  { "message": "Conta Atualizada" }