from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

database_url = os.getenv("MONGODB_URI")
client = MongoClient(database_url, tlsCAFile=certifi.where())
db = client["coursenest"]
users_collection = db["usersDB"]

class User:
    @staticmethod
    def get_all():
        users = list(users_collection.find({}, {"_id": 0}))
        return users

    @staticmethod
    def get_by_id(user_id):
        user = users_collection.find_one({"id": int(user_id)}, {"_id": 0})
        return user

    @staticmethod
    def create(user_data):
        last_user = users_collection.find_one(sort=[("id", -1)])
        next_id = (last_user["id"] + 1) if last_user else 1
        
        new_user = {
            "id": next_id,
            "username": user_data.get("username"),
            "email": user_data.get("email")
        }
        
        users_collection.insert_one(new_user)
        return next_id
    @staticmethod
    def update(user_id, user_data):
        update_fields = {}
        if "username" in user_data:
            update_fields["username"] = user_data["username"]
        if "email" in user_data:
            update_fields["email"] = user_data["email"]
            
        result = users_collection.update_one(
            {"id": int(user_id)},
            {"$set": update_fields}
        )
        return result.modified_count > 0

    @staticmethod
    def delete(user_id):
        result = users_collection.delete_one({"id": int(user_id)})
        return result.deleted_count > 0
