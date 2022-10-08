from pydantic import BaseModel


class ContaSchema(BaseModel):
    idConta: int | None
    saldoConta: float
    qtdAtivos: int
    valorAtivos: float
    precoMedio: float
    nomeAtivo: str
    
    class Config:
        orm_mode = True

