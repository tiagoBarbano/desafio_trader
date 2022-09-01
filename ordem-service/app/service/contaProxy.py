import aiohttp
from opentelemetry.instrumentation.aiohttp_client import create_trace_config
        

async def contaProxy(idConta: int):
    try:
        params = {'id' : idConta }
            
        async with aiohttp.ClientSession(trace_configs=[create_trace_config()]) as session:
            async with session.get("http://localhost:8003/", params=params, ssl=False) as response:
                if response.status != 200:
                    return 1 
                resposta = await response.json()
                
        return resposta
    except Exception as ex:
        raise Exception("Problema na consulta de Saldo: " + str(ex))