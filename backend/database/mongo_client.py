# database/mongo_client.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from config.settings import settings
from models.user import User
from models.company import Company

client: AsyncIOMotorClient | None = None


async def init_db():
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    database = client[settings.DATABASE_NAME]

    await init_beanie(
        database=database,
        document_models=[User, Company],
    )