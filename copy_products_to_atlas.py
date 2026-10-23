
from pymongo import MongoClient
from beauty.db_connection import client as atlas_client
from beauty.db_connection import db as atlas_db

# Local MongoDB connection
local_client = MongoClient(
    "mongodb://localhost:27017/",
    serverSelectionTimeoutMS=5000,
)

COLLECTIONS = [
    "Products",
    "Users",
    "Cart",
    "Orders",
    "Reviews",
    "Followers",
]


def copy_collection(local_db, collection_name):
    source = local_db[collection_name]
    destination = atlas_db[collection_name]

    documents = list(source.find())

    print(f"\n{collection_name}")
    print("Local MongoDB documents:", len(documents))

    for document in documents:
        destination.replace_one(
            {"_id": document["_id"]},
            document,
            upsert=True,
        )

    print(
        "Atlas documents:",
        destination.count_documents({})
    )


try:
    # Verify connections
    local_client.admin.command("ping")
    atlas_client.admin.command("ping")

    local_db = local_client["Beauty_store"]

    print("Local MongoDB and Atlas connections successful.")

    for collection_name in COLLECTIONS:
        copy_collection(local_db, collection_name)

    print("\nAll collection migration steps completed!")

except Exception as error:
    print("\nMigration failed:", type(error).__name__)
    print("Check your MongoDB connections and permissions.")

finally:
    local_client.close()


