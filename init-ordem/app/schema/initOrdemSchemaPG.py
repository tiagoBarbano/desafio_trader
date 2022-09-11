import enum
from pydantic import BaseModel


class Transacao(str, enum.Enum):
    COMPRA = "COMPRA"
    VENDA = "VENDA"

class OrderSchema(BaseModel):
    id: int | None
    tipoTransacao: Transacao
    precoMedio: float
    qtdOrdem: int
    idConta: int
    myuuid: str | None
    
    class Config:
        orm_mode = True

