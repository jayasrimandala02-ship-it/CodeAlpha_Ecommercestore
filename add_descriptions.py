
from beauty.db_connection import products_collection

result = products_collection.update_many(
    {
        "$or": [
            {"description": {"$exists": False}},
            {"description": None},
            {"description": ""}
        ]
    },
    [
        {
            "$set": {
                "description": {
                    "$concat": [
                        "Explore this ",
                        {"$ifNull": ["$category", "beauty"]},
                        " from ",
                        {"$ifNull": ["$brand", "our collection"]},
                        ". Check the product label for ingredients and directions before use."
                    ]
                }
            }
        }
    ]
)

print("Products matched:", result.matched_count)
print("Products updated:", result.modified_count)
