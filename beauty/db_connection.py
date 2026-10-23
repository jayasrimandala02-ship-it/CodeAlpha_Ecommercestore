
import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient

# Load the .env file from the main VELOURA project folder
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# MongoDB connection settings
MONGO_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.environ.get("MONGODB_DB_NAME", "Beauty_store")

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
)

# Database and collections
db = client[DATABASE_NAME]

products_collection = db["Products"]
users_collection = db["Users"]
orders_collection = db["Orders"]
cart_collection = db["Cart"]
reviews_collection = db["Reviews"]
followers_collection = db["Followers"]
