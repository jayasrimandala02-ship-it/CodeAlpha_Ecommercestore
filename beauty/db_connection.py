
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# =====================================================
# MONGODB CONNECTION
# =====================================================

MONGO_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb://localhost:27017/"
)

DATABASE_NAME = os.environ.get(
    "MONGODB_DB_NAME",
    "Beauty_store"
)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
)


# =====================================================
# DATABASE
# =====================================================

db = client[DATABASE_NAME]


# =====================================================
# COLLECTIONS
# =====================================================

products_collection = db["Products"]
users_collection = db["Users"]
orders_collection = db["Orders"]
cart_collection = db["Cart"]
reviews_collection = db["Reviews"]
followers_collection = db["Followers"]

