from fastapi import APIRouter, HTTPException, status
from aredis_om import get_redis_connection, JsonModel, Field, Migrator


router = APIRouter()

redis = get_redis_connection(host="localhost", port=6379, decode_responses=True, db=0)

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
        conta = await Conta.find(Conta.idConta == id).first()
        return conta.saldoConta
    except Exception as ex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ex))

@router.get("/pk/{pk}")
async def get_conta_by_pk(pk: str):
    conta = await Conta.get(pk)
    return conta

@router.post('/')
async def create(request: Conta):
    await request.save()
    return  request