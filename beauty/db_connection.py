from pymongo import MongoClient
from pymongo.errors import PyMongoError


# =====================================================
# MONGODB CONNECTION
# =====================================================

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "Beauty_store"

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
)

# Check whether MongoDB is reachable.
try:
    client.admin.command("ping")
    print("MongoDB connected successfully!")
except PyMongoError as error:
    print("MongoDB connection failed:", error)
    raise


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
