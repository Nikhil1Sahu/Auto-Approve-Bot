import os
import random
import asyncio
import contextlib
from typing import Dict, Any, List

from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import InputFile
from config import ADMIN, PICS, LOG_CHANNEL
from Script import text
from .db import tb
from .fsub import get_fsub

# ------------------ Helpers ------------------
ADMIN_ONLY_TEXT = "❌ This command doesn't exist"

def is_admin_id(uid: int) -> bool:
    return uid == ADMIN

async def ensure_admin(client: Client, message: Message) -> bool:
    if is_admin_id(message.from_user.id):
        return True
    # Non-admins always see “doesn't exist” for admin commands
    await message.reply_text(ADMIN_ONLY_TEXT)
    return False

def kb(rows: List[List[Any]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(rows)

# ------------------ START ------------------
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    if await tb.get_user(message.from_user.id) is None:
        await tb.add_user(message.from_user.id, message.from_user.first_name)
        bot = await client.get_me()
        await client.send_message(
            LOG_CHANNEL,
            text.LOG.format(
                message.from_user.id,
                getattr(message.from_user, "dc_id", "N/A"),
                message.from_user.first_name or "N/A",
                f"@{message.from_user.username}" if message.from_user.username else "N/A",
                bot.username
            )
        )
    if await get_fsub(client, message) is False:
        return
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=text.START.format(message.from_user.mention),
        reply_markup=kb([
            [InlineKeyboardButton('⇆ Add me to your group ⇆',
                                  url="https://telegram.me/QuickAcceptBot?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ℹ️ About', callback_data='about'),
             InlineKeyboardButton('📚 Help', callback_data='help')],
            [InlineKeyboardButton('⇆ Add me to your channel ⇆',
                                  url="https://telegram.me/QuickAcceptBot?startchannel=true&admin=invite_users")]
        ])
    )

# ------------------ HELP ------------------
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message: Message):
    reply = await message.reply(
        text=("❓ <b>Having Trouble?</b>\n\n"
              "Watch the tutorial video to understand features clearly."),
        reply_markup=kb([
            [InlineKeyboardButton("🎬 Watch Tutorial", url="https://youtu.be/_n3V0gFZMh8")],
        ])
    )
    await asyncio.sleep(300)
    with contextlib.suppress(Exception):
        await reply.delete()
        await message.delete()

# ------------------ Global Thumbnail ------------------
@Client.on_message(filters.command("setthumb") & filters.private)
async def set_thumb(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("Reply to a photo with /setthumb to set it as the global thumbnail.")

    photo = message.reply_to_message.photo

    # save in DB with fixed key "global_thumb"
    meta = {
        "file_id": photo.file_id,
        "mime": "image/jpeg",
        "width": getattr(photo, "width", 0),
        "height": getattr(photo, "height", 0),
        "size_bytes": getattr(photo, "file_size", 0)
    }
    await tb.save_named_thumb(message.from_user.id, "global_thumb", meta)

    await message.reply_text("✅ Global thumbnail saved successfully.")

@Client.on_message(filters.command("delthumb") & filters.private)
async def del_thumb(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    await tb.delete_named_thumb(message.from_user.id, "global_thumb")
    await message.reply_text("🗑️ Global thumbnail removed.")

# ------------------ /post (entry) ------------------
@Client.on_message(filters.command("post") & filters.private)
async def post_entry(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    chans = await tb.list_channels()
    if not chans:
        return await message.reply_text("Make the bot an admin in the channel where you want to post.")

    session = {
        "stage": "channels",
        "channel_id": None,
        "items": []
    }
    await tb.set_session(message.from_user.id, session)

    rows = [[InlineKeyboardButton(c["title"], callback_data=f"post:chan:{c['chat_id']}")] for c in chans]
    await message.reply_text("Select a channel to post:", reply_markup=kb(rows))

# ------------------ Collector ------------------
@Client.on_message(filters.private & ~filters.command(["start", "help", "setthumb", "delthumb", "post"]))
async def collect_items(client: Client, message: Message):
    uid = message.from_user.id
    session = await tb.get_session(uid)
    if not session or session.get("stage") != "collect":
        return

    item: Dict[str, Any] | None = None

    if message.text:
        item = {"type": "text", "text": message.text}
    elif message.document:
        doc = message.document
        item = {
            "type": "document",
            "file_id": doc.file_id,
            "file_name": doc.file_name,
            "mime": doc.mime_type or "",
            "caption": message.caption or "",
            "is_pdf": (doc.mime_type == "application/pdf")
        }
    elif message.photo:
        item = {"type": "photo", "file_id": message.photo.file_id, "caption": message.caption or ""}
    elif message.video:
        item = {"type": "video", "file_id": message.video.file_id, "caption": message.caption or ""}
    elif message.sticker:
        item = {"type": "sticker", "file_id": message.sticker.file_id}
    else:
        return await message.reply_text("This message type is not supported for posting yet.")

    session["items"].append(item)
    await tb.set_session(uid, session)

    await message.reply_text(
        "Added. Send more or continue.",
        reply_markup=kb([
            [InlineKeyboardButton("Add", callback_data="post:add"),
             InlineKeyboardButton("Continue", callback_data="post:continue")]
        ])
    )

# ------------------ Unknown Command ------------------
@Client.on_message(filters.command(["start", "help", "setthumb", "delthumb", "post"]) & filters.private)
async def known_commands(client, message: Message):
    # do nothing, handled above
    return

@Client.on_message(filters.command() & filters.private)
async def unknown_command(client: Client, message: Message):
    await message.reply_text(ADMIN_ONLY_TEXT)
