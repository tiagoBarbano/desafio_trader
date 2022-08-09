import asyncio
from app.service.createdOrderQueue import createdOrderQueue
from app.service.newOrderQueue import newOrderQueue


async def init_Orquestrador():
    await step1()

async def step1():
    
    task1 = asyncio.create_task(newOrderQueue())
    task2 = asyncio.create_task(createdOrderQueue())
    
    await asyncio.gather(task1,task2)

