from sqlalchemy import Column, String, Integer, Float, DateTime
from app.database import Base


class OrdenModel(Base):
    __tablename__ = "ordem"

    id = Column(Integer, autoincrement=True, primary_key=True)
    myuuid = Column(String)
    tipotransacao = Column(String)
    precomedio = Column(Float)
    qtdordem = Column(Integer)
    idconta = Column(Integer)
    dataordem = Column(DateTime)
    nomeativo = Column(String)
    statusordem = Column(String)
    valorordem = Column(Float)
    