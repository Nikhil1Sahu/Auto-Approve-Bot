import os
from typing import Any
from motor import motor_asyncio
from config import DB_URI, DB_NAME

# ------------------ CHECK ENV VARS ------------------
if not DB_URI or not DB_NAME:
    raise ValueError("DB_URI or DB_NAME not set in environment variables")

# ------------------ DATABASE CONNECTION ------------------
client = motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]

# ------------------  CLASS ------------------
class Techifybots:
    def __init__(self):
        self.users = db["users"]
        self.cache: dict[int, dict[str, Any]] = {}

    # ------------------- USER FUNCTIONS -------------------
    async def add_user(self, user_id: int, name: str) -> dict[str, Any] | None:
        try:
            user: dict[str, Any] = {
                "user_id": user_id,
                "name": name,
                "session": None,
                "thumbnail": None,
                "thumbnails": {}  # store multiple thumbnails {name: file_id}
            }
            await self.users.insert_one(user)
            self.cache[user_id] = user
            return user
        except Exception as e:
            print("Error in add_user:", e)

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        try:
            if user_id in self.cache:
                return self.cache[user_id]
            user = await self.users.find_one({"user_id": user_id})
            if user:
                self.cache[user_id] = user
            return user
        except Exception as e:
            print("Error in get_user:", e)
            return None

    async def set_session(self, user_id: int, session: Any) -> bool:
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"session": session}}
            )
            if user_id in self.cache:
                self.cache[user_id]["session"] = session
            return result.modified_count > 0
        except Exception as e:
            print("Error in set_session:", e)
            return False

    async def get_session(self, user_id: int) -> Any | None:
        try:
            user = await self.get_user(user_id)
            return user.get("session") if user else None
        except Exception as e:
            print("Error in get_session:", e)
            return None

    async def get_all_users(self) -> list[dict[str, Any]]:
        try:
            users: list[dict[str, Any]] = []
            async for user in self.users.find():
                users.append(user)
            return users
        except Exception as e:
            print("Error in get_all_users:", e)
            return []

    async def delete_user(self, user_id: int) -> bool:
        try:
            result = await self.users.delete_one({"user_id": user_id})
            self.cache.pop(user_id, None)
            return result.deleted_count > 0
        except Exception as e:
            print("Error in delete_user:", e)
            return False

    # ------------------- SINGLE THUMB (legacy) -------------------
    async def save_thumb(self, user_id: int, file_id: str) -> bool:
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"thumbnail": file_id}},
                upsert=True
            )
            if user_id in self.cache:
                self.cache[user_id]["thumbnail"] = file_id
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print("Error in save_thumb:", e)
            return False

    async def get_thumb(self, user_id: int) -> str | None:
        try:
            user = await self.get_user(user_id)
            return user.get("thumbnail") if user else None
        except Exception as e:
            print("Error in get_thumb:", e)
            return None

    async def clear_thumb(self, user_id: int) -> bool:
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$unset": {"thumbnail": ""}}
            )
            if user_id in self.cache and "thumbnail" in self.cache[user_id]:
                self.cache[user_id]["thumbnail"] = None
            return result.modified_count > 0
        except Exception as e:
            print("Error in clear_thumb:", e)
            return False

    # ------------------- MULTI-THUMB FUNCTIONS -------------------
    async def save_named_thumb(self, user_id: int, thumb_name: str, file_id: str) -> bool:
        """Save a thumbnail with a custom name"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$set": {f"thumbnails.{thumb_name}": file_id}},
                upsert=True
            )
            if user_id in self.cache:
                if "thumbnails" not in self.cache[user_id]:
                    self.cache[user_id]["thumbnails"] = {}
                self.cache[user_id]["thumbnails"][thumb_name] = file_id
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print("Error in save_named_thumb:", e)
            return False

    async def get_named_thumbs(self, user_id: int) -> dict[str, str]:
        """Get all thumbnails {name: file_id}"""
        try:
            user = await self.get_user(user_id)
            return user.get("thumbnails", {}) if user else {}
        except Exception as e:
            print("Error in get_named_thumbs:", e)
            return {}

    async def delete_named_thumb(self, user_id: int, thumb_name: str) -> bool:
        """Delete a specific named thumbnail"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$unset": {f"thumbnails.{thumb_name}": ""}}
            )
            if user_id in self.cache and "thumbnails" in self.cache[user_id]:
                self.cache[user_id]["thumbnails"].pop(thumb_name, None)
            return result.modified_count > 0
        except Exception as e:
            print("Error in delete_named_thumb:", e)
            return False

    async def clear_all_named_thumbs(self, user_id: int) -> bool:
        """Delete all thumbnails for a user"""
        try:
            result = await self.users.update_one(
                {"user_id": user_id},
                {"$unset": {"thumbnails": ""}}
            )
            if user_id in self.cache and "thumbnails" in self.cache[user_id]:
                self.cache[user_id]["thumbnails"] = {}
            return result.modified_count > 0
        except Exception as e:
            print("Error in clear_all_named_thumbs:", e)
            return False

# ------------------ INSTANCE ------------------
tb = Techifybots()
