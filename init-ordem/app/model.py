from sqlalchemy import Column, String, Integer, Float

from app.database import Base


class OrderModel(Base):
    __tablename__ = "initorder"

    id = Column(Integer, autoincrement=True, primary_key=True)
    tipotransacao = Column(String)
    precomedio = Column(Float)
    qtdordem = Column(Integer)
    idconta = Column(Integer)
    myuuid = Column(String)
