from sqlalchemy import Column, String, Integer, Float

from app.database import Base


class ContaModel(Base):
    __tablename__ = "conta"

    idconta = Column(Integer, autoincrement=True, primary_key=True)
    saldoconta = Column(Float)
    qtdativos = Column(Integer)
    valorativos = Column(Float)
    precomedio = Column(Float)
    nomeativo = Column(String)
