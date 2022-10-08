from app.database import async_session
from app.model import ContaModel
from app.schema import ContaSchema
from fastapi import APIRouter, HTTPException
from sqlalchemy.future import select
from typing import AsyncGenerator
from sqlalchemy.exc import SQLAlchemyError


router = APIRouter()

@router.post('/')
async def create(conta: ContaSchema):
    contaModel = ContaModel(saldoconta=conta.saldoConta,
                            qtdativos=conta.qtdAtivos,
                            valorativos=conta.valorAtivos,
                            precomedio=conta.precoMedio,
                            nomeativo=conta.nomeAtivo)
    
    async with async_session() as session:
        session.add(contaModel)
        await session.commit()
        await session.close()
        
    return contaModel
        
@router.get("/contas")
async def get_contas():
    query = select(ContaModel)
    async with async_session() as session:
        contas = await session.execute(query)
        contas = contas.scalars().all()
        await session.commit()
        await session.close()    
        return contas

@router.get("/")
async def get_conta_by_id(id: int):
    query = select(ContaModel).where(ContaModel.idconta == id)
    async with async_session() as session:
        contas = await session.execute(query)
        conta = contas.scalar_one_or_none()
        
        
        return { "SaldoConta": conta.saldoconta, 
                "ValorAtivos": conta.valorativos } 

@router.post('/credita-conta')
async def creditaConta(idConta: int, qtdAtivos: int, valorAtivos: float, nomeAtivo: str):
    query = select(ContaModel).where(ContaModel.idconta == idConta)
    async with async_session() as session:
        contas = await session.execute(query)
        conta = contas.scalar_one_or_none()
    
        conta.qtdativos = conta.qtdativos + qtdAtivos
        conta.nomeativo = nomeAtivo
        conta.valorativos = conta.valorativos + valorAtivos
        conta.saldoconta = conta.saldoconta - valorAtivos
        conta.precomedio = conta.valorativos / conta.qtdativos
        
        session.add(conta)
        await session.commit()
        await session.close()
    
    return  { "message": "Conta Atualizada" }   


@router.post('/debita-conta')
async def debitaConta(idConta: int, qtdAtivos: int, valorAtivos: float, nomeAtivo: str):
    query = select(ContaModel).where(ContaModel.idconta == idConta)
    async with async_session() as session:
        contas = await session.execute(query)
        conta = contas.scalar_one_or_none()
    
        conta.qtdativos = conta.qtdativos - qtdAtivos
        conta.nomeativo = nomeAtivo
        conta.valorativos = conta.valorativos - valorAtivos
        conta.saldoconta = conta.saldoconta + valorAtivos
        conta.precomedio = conta.valorativos / conta.qtdativos
        
        session.add(conta)
        await session.commit()
        await session.close()
    
    return  { "message": "Conta Atualizada" }   

# Dependency
async def get_db() -> AsyncGenerator:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as sql_ex:
            await session.rollback()
            raise sql_ex
        except HTTPException as http_ex:
            await session.rollback()
            raise http_ex
        finally:
            await session.close()