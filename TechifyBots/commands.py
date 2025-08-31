import os
import random
import asyncio
from typing import Dict, Any, List

from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

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
@Client.on_message(filters.command("start"))
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
            [InlineKeyboardButton('⇆ Add me to your group ⇆', url="https://telegram.me/QuickAcceptBot?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ℹ️ About', callback_data='about'),
             InlineKeyboardButton('📚 Help', callback_data='help')],
            [InlineKeyboardButton('⇆ Add me to your channel ⇆', url="https://telegram.me/QuickAcceptBot?startchannel=true&admin=invite_users")]
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

# ------------------ /setthumb ------------------
# Usage: reply to a JPEG photo with /setthumb <name>
import contextlib

@Client.on_message(filters.command("setthumb") & filters.private)
async def set_thumb(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    parts = message.text.split(maxsplit=1)
    thumb_name = parts[1].strip() if len(parts) > 1 else None
    replied = message.reply_to_message

    if not thumb_name or not replied or not replied.photo:
        return await message.reply_text(
            "Tag a photo. It must be in JPEG format, be under 200 KB in size, and not exceed 320 pixels in width or height."
        )

    p = replied.photo  # Telegram photos are JPEG
    width = getattr(p, "width", 0) or 0
    height = getattr(p, "height", 0) or 0
    size_bytes = getattr(p, "file_size", 0) or 0
    mime = "image/jpeg"  # Telegram photos are JPEG

    if not (mime == "image/jpeg" and size_bytes < 200 * 1024 and width <= 320 and height <= 320):
        return await message.reply_text(
            "❌ Failed — photo must be in JPEG format, be under 200 KB in size, and not exceed 320 pixels in width or height."
        )

    meta = {
        "file_id": p.file_id,
        "mime": mime,
        "width": width,
        "height": height,
        "size_bytes": size_bytes
    }
    await tb.save_named_thumb(message.from_user.id, thumb_name, meta)
    await message.reply_text("Thumbnail name saved successfully.")

# ------------------ /thumbnails ------------------
@Client.on_message(filters.command("thumbnails") & filters.private)
async def thumbnails_cmd(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    thumbs = await tb.list_named_thumbs(message.from_user.id)
    if not thumbs:
        return await message.reply_text("No thumbnails found.")

    rows = []
    for t in thumbs:
        rows.append([InlineKeyboardButton(t["name"], callback_data=f"thumb:view:{t['name']}")])
    await message.reply_text("Saved thumbnails:", reply_markup=kb(rows))

# ------------------ /clearthumb ------------------
@Client.on_message(filters.command("clearthumb") & filters.private)
async def clearthumb_cmd(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    parts = message.text.split(maxsplit=1)
    thumbs = await tb.list_named_thumbs(message.from_user.id)

    if len(parts) == 1:
        if not thumbs:
            return await message.reply_text("No thumbnails found.")
        rows = [[InlineKeyboardButton(t["name"], callback_data=f"clearthumb:ask:{t['name']}")] for t in thumbs]
        return await message.reply_text("Choose which thumbnail you want to delete.", reply_markup=kb(rows))

    # /clearthumb <name> -> ask confirm
    name = parts[1].strip()
    if not any(t["name"] == name for t in thumbs):
        return await message.reply_text("Thumbnail not found.")
    await message.reply_text(
        "Do you really want to delete this thumbnail?",
        reply_markup=kb([
            [InlineKeyboardButton("Yes", callback_data=f"clearthumb:yes:{name}"),
             InlineKeyboardButton("No", callback_data=f"clearthumb:no:{name}")]
        ])
    )

# ------------------ /post (entry) ------------------
@Client.on_message(filters.command("post") & filters.private)
async def post_entry(client: Client, message: Message):
    if not await ensure_admin(client, message):
        return

    # Stage A — list channels the bot knows (registry)
    chans = await tb.list_channels()
    if not chans:
        return await message.reply_text("Make the bot an admin in the channel where you want to post.")

    # init session
    session = {
        "stage": "channels",
        "channel_id": None,
        "items": [],               # will hold dicts
        "pdf_thumb_name": None
    }
    await tb.set_session(message.from_user.id, session)

    rows = [[InlineKeyboardButton(c["title"], callback_data=f"post:chan:{c['chat_id']}")] for c in chans]
    await message.reply_text("Select a channel to post:", reply_markup=kb(rows))

# ------------------ Collector while in stage=collect ------------------
@Client.on_message(filters.private & ~filters.command(["start", "help", "setthumb", "thumbnails", "clearthumb", "post"]))
async def collect_items(client: Client, message: Message):
    uid = message.from_user.id
    session = await tb.get_session(uid)
    if not session or session.get("stage") != "collect":
        return  # ignore normal chat

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

# ------------------ Fallback unknown command ------------------
@Client.on_message(filters.command & filters.private)
async def unknown_command(client: Client, message: Message):
    # allow known commands to pass
    known = {"start", "help", "setthumb", "thumbnails", "clearthumb", "post"}
    if message.command and message.command[0].lower() in known:
        return
    # show same text for everyone per spec
    await message.reply_text(ADMIN_ONLY_TEXT)
