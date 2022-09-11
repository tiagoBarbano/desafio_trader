from app.database import async_session
from app.model import OrdenModel
from app.schema.order_schema import Order, Ativo, Status, Transacao, OrderSchema
from fastapi import APIRouter, HTTPException
from sqlalchemy.future import select


async def save(ordem: OrderSchema):
    ordemModel = OrdenModel(myuuid=ordem.myUUID,
                            tipotransacao=ordem.tipoTransacao,
                            precomedio=ordem.precoMedio,
                            qtdordem=ordem.qtdOrdem,
                            idconta=ordem.idConta,
                            dataordem=ordem.dataOrdem,
                            nomeativo=ordem.nomeAtivo,
                            statusordem=ordem.statusOrdem,
                            valorordem=ordem.valorOrdem)
    async with async_session() as session:
        session.add(ordemModel)
        await session.commit()
        await session.close()
        
    return ordemModel

async def saveModel(ordem: OrdenModel):
    async with async_session() as session:
        session.add(ordem)
        await session.commit()
        await session.close()
        
    return ordem

async def get_order_pendings(id: int, tipoTransacao: Transacao, statusOrdem: Status):
    query = select(OrdenModel).where(OrdenModel.idconta == id, 
                                     OrdenModel.tipotransacao == tipoTransacao, 
                                     OrdenModel.statusordem == statusOrdem)
    async with async_session() as session:
        ordens = await session.execute(query)
        retorno = ordens.scalars().all()
        await session.commit()
        await session.close()
    
    return retorno

async def get_order_to_booking(id: int, tipoTransacao: Transacao, statusOrdem: Status, valorOrdem: float):
    query = select(OrdenModel).where(OrdenModel.idconta != id, 
                                     OrdenModel.tipotransacao == tipoTransacao, 
                                     OrdenModel.statusordem == statusOrdem,
                                     OrdenModel.valorordem == valorOrdem)
    async with async_session() as session:
        ordens = await session.execute(query)
        retorno = ordens.scalars().all()
        await session.commit()
        await session.close()
    
    return retorno