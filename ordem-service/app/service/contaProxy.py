import aiohttp
from opentelemetry.instrumentation.aiohttp_client import create_trace_config
from app.config import PROXY_CONTA, PROXY_DEBITO, PROXY_CREDITO
        

async def contaProxy(idConta: int):
    try:
        params = {'id' : idConta }
            
        async with aiohttp.ClientSession(trace_configs=[create_trace_config()]) as session:
            async with session.get(PROXY_CONTA, params=params, ssl=False) as response:
                if response.status != 200:
                    return -1 
                resposta = await response.json()
                
        return resposta
    except Exception as ex:
        raise Exception("Problema na consulta de Saldo: " + str(ex))
    
async def contaProxyCredita(idConta: int, qtdAtivos: int, valorAtivos: float, nomeAtivo: str):
    try:
        params = {'idConta' : idConta,
                  'qtdAtivos' : qtdAtivos,
                  'valorAtivos' : valorAtivos,
                  'nomeAtivo' : nomeAtivo}
            
        async with aiohttp.ClientSession(trace_configs=[create_trace_config()]) as session:
            async with session.post(PROXY_CREDITO, params=params, ssl=False) as response:
                if response.status != 200:
                    return False
        return True
    except Exception as ex:
        raise Exception("Problema na consulta de Saldo: " + str(ex))
    
async def contaProxyDebita(idConta: int, qtdAtivos: int, valorAtivos: float, nomeAtivo: str):
    try:
        params = {'idConta' : idConta,
                  'qtdAtivos' : qtdAtivos,
                  'valorAtivos' : valorAtivos,
                  'nomeAtivo' : nomeAtivo}
            
        async with aiohttp.ClientSession(trace_configs=[create_trace_config()]) as session:
            async with session.post(PROXY_DEBITO, params=params, ssl=False) as response:
                if response.status != 200:
                    return False              
        return True
    except Exception as ex:
        raise Exception("Problema na consulta de Saldo: " + str(ex))        