from app.database import async_session
from app.model import OrderModel


async def saveInitOrder(order: OrderModel):
    async with async_session() as session:
        session.add(order)
        await session.commit()
        await session.close()