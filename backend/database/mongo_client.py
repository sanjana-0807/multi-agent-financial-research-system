# database/mongo_client.py
from models.report import Report
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from config.settings import settings

from models.user import User
from models.company import Company
from models.comparison_result import ComparisonResult
from models.document import DocumentModel
from models.red_flag import RedFlagResult
from models.workspace import Workspace

client: AsyncIOMotorClient | None = None


async def init_db():
    global client

    client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        connectTimeoutMS=30000,
        serverSelectionTimeoutMS=30000,
        socketTimeoutMS=30000,
    )

    database = client[
        settings.DATABASE_NAME
    ]

    await init_beanie(
        database=database,
        document_models=[
            User,
            Company,
            ComparisonResult,
            DocumentModel,
            RedFlagResult,
            Workspace,
            Report,
        ],
    )