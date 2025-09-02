from typing import Any
from config import DB_URI, DB_NAME
from motor import motor_asyncio
import os

client: motor_asyncio.AsyncIOMotorClient[Any] = motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client[DB_NAME]

class Techifybots:
    def __init__(self):
        self.users = db["users"]
        self.settings = db["settings"]   # stores bot-wide settings (global thumb, channels list, etc.)
        self.cache: dict[int, dict[str, Any]] = {}
        self.settings_cache: dict[str, Any] = {}

    # -------------------- USER FUNCTIONS --------------------
    async def add_user(self, user_id: int, name: str) -> dict[str, Any] | None:
        try:
            user: dict[str, Any] = {"user_id": user_id, "name": name, "session": None}
            await self.users.update_one(
                {"user_id": user_id}, {"$setOnInsert": user}, upsert=True
            )
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
                {"$set": {"session": session}},
                upsert=True
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

    # -------------------- SETTINGS FUNCTIONS --------------------
    async def set_setting(self, key: str, value: Any) -> None:
        try:
            await self.settings.update_one(
                {"key": key},
                {"$set": {"value": value}},
                upsert=True
            )
            self.settings_cache[key] = value
        except Exception as e:
            print("Error in set_setting:", e)

    async def get_setting(self, key: str) -> Any | None:
        try:
            if key in self.settings_cache:
                return self.settings_cache[key]
            setting = await self.settings.find_one({"key": key})
            if setting:
                self.settings_cache[key] = setting["value"]
                return setting["value"]
            return None
        except Exception as e:
            print("Error in get_setting:", e)
            return None

    # -------------------- GLOBAL THUMBNAIL HELPERS --------------------
    async def set_global_thumb(self, file_id_or_path: str):
        """Save global thumbnail (file_id from Telegram or static path)."""
        await self.set_setting("global_thumb", file_id_or_path)

    async def get_global_thumb(self) -> str | None:
        """Return global thumbnail, fallback to assets/thumb.jpg if none set."""
        thumb = await self.get_setting("global_thumb")
        if thumb:
            return thumb

        fallback = os.path.join("assets", "thumb.jpg")
        return fallback if os.path.exists(fallback) else None

    # -------------------- CHANNEL MANAGEMENT --------------------
    async def add_channel(self, chat_id: int, title: str):
        """Save allowed channel to DB (for posting)."""
        try:
            channels = await self.get_channels()
            if not any(c["chat_id"] == chat_id for c in channels):
                channels.append({"chat_id": chat_id, "title": title})
                await self.set_setting("channels", channels)
        except Exception as e:
            print("Error in add_channel:", e)

    async def get_channels(self) -> list[dict[str, Any]]:
        """Get list of allowed channels (for post menu)."""
        try:
            channels = await self.get_setting("channels")
            return channels if channels else []
        except Exception as e:
            print("Error in get_channels:", e)
            return []

    async def remove_channel(self, chat_id: int):
        """Remove channel from allowed list."""
        try:
            channels = await self.get_channels()
            channels = [c for c in channels if c["chat_id"] != chat_id]
            await self.set_setting("channels", channels)
        except Exception as e:
            print("Error in remove_channel:", e)


tb = Techifybots()
