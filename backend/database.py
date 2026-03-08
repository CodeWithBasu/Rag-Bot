import os
import motor.motor_asyncio
from dotenv import load_dotenv

load_dotenv()

# MongoDB Connection Configuration
# Default to localhost if not provided
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "rag_bot")

# Create Motor Client
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client[DB_NAME]

async def get_db():
    return db

# Collections can be accessed via db['collection_name']
