from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import FloodWait
import asyncio
import os
from config import ADMIN
from TechifyBots.db import tb  # Techifybots instance

# Temporary in-memory storage for post workflow
post_sessions = {}  # {admin_id: {"channel": id, "messages": [], "step": str, "set_thumb": bool, "time": float}}

# Auto-expire sessions after X minutes
SESSION_TIMEOUT = 600  # 10 min


# --------------- FloodWait safe sender ---------------
async def safe_send(client, func, *args, **kwargs):
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            print(f"[FloodWait] sleeping {e.value}s")
            await asyncio.sleep(e.value)
        except Exception as ex:
            print(f"[SendError] {ex}")
            return None


# --------------- /post command ---------------
@Client.on_message(filters.command("post") & filters.user([ADMIN]))
async def start_post(client: Client, message: Message):
    admin_id = message.from_user.id

    # Fetch allowed channels from DB
    channels = await tb.get_channels()
    if not channels:
        return await message.reply("⚠️ No channels registered. Please add channels first.")

    # Build channel selection buttons
    keyboard = [
        [InlineKeyboardButton(c["title"], callback_data=f"post_channel:{c['chat_id']}")]
        for c in channels
    ]
    await message.reply(
        "📢 Select a channel to post in:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# --------------- Handle channel selection ---------------
@Client.on_callback_query(filters.regex(r"^post_channel:(-?\d+)$"))
async def select_channel(client, callback_query):
    admin_id = callback_query.from_user.id
    channel_id = int(callback_query.data.split(":")[1])

    # Init session
    post_sessions[admin_id] = {
        "channel": channel_id,
        "messages": [],
        "step": "collecting",
        "set_thumb": False,
        "time": asyncio.get_event_loop().time()
    }

    await callback_query.message.edit_text(
        "✅ Channel selected!\n\nNow send me one or multiple messages you want to include in the post."
    )


# --------------- Collect messages ---------------
@Client.on_message(filters.user([ADMIN]) & ~filters.command("post"))
async def collect_post_content(client, message: Message):
    admin_id = message.from_user.id

    # check session active
    session = post_sessions.get(admin_id)
    if not session or session["step"] != "collecting":
        return

    # Save message reference
    session["messages"].append(message)

    # Show add/continue buttons
    keyboard = [
        [InlineKeyboardButton("➕ Add more", callback_data="post_add")],
        [InlineKeyboardButton("✅ Continue", callback_data="post_continue")],
        [InlineKeyboardButton("❌ Cancel", callback_data="post_cancel")]
    ]
    await message.reply("Message added to post.", reply_markup=InlineKeyboardMarkup(keyboard))


# --------------- Add more ---------------
@Client.on_callback_query(filters.regex(r"^post_add$"))
async def add_more(client, callback_query):
    await callback_query.message.edit_text("📩 Send me more messages to include in the post.")


# --------------- Continue (check for PDFs) ---------------
@Client.on_callback_query(filters.regex(r"^post_continue$"))
async def continue_post(client, callback_query):
    admin_id = callback_query.from_user.id
    session = post_sessions.get(admin_id)

    if not session:
        return await callback_query.answer("Session expired.", show_alert=True)

    # Detect any PDF documents
    has_pdf = any(
        getattr(msg, "document", None) and msg.document.mime_type == "application/pdf"
        for msg in session["messages"]
    )

    if has_pdf:
        keyboard = [
            [InlineKeyboardButton("🖼️ Set thumb", callback_data="post_set_thumb")],
            [InlineKeyboardButton("✅ Continue", callback_data="post_ready")],
            [InlineKeyboardButton("❌ Cancel", callback_data="post_cancel")]
        ]
        await callback_query.message.edit_text(
            "📂 I detected PDF(s) in your post.\nDo you want to apply the global thumbnail?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await show_ready_page(callback_query.message, admin_id)


# --------------- Set thumbnail ---------------
@Client.on_callback_query(filters.regex(r"^post_set_thumb$"))
async def set_thumb(client, callback_query):
    admin_id = callback_query.from_user.id
    session = post_sessions.get(admin_id)

    if not session:
        return await callback_query.answer("Session expired.", show_alert=True)

    # Mark that global thumb should be applied
    session["set_thumb"] = True
    await show_ready_page(callback_query.message, admin_id)


# --------------- Ready page ---------------
async def show_ready_page(message, admin_id):
    keyboard = [
        [InlineKeyboardButton("📤 Send", callback_data="post_send")],
        [InlineKeyboardButton("🔙 Back", callback_data="post_continue")],
        [InlineKeyboardButton("❌ Cancel", callback_data="post_cancel")]
    ]
    await message.edit_text("✅ Post is ready to publish!", reply_markup=InlineKeyboardMarkup(keyboard))


# --------------- Cancel ---------------
@Client.on_callback_query(filters.regex(r"^post_cancel$"))
async def cancel_post(client, callback_query):
    admin_id = callback_query.from_user.id
    post_sessions.pop(admin_id, None)
    await callback_query.message.edit_text("❌ Post creation cancelled.")


# --------------- Send post ---------------
@Client.on_callback_query(filters.regex(r"^post_send$"))
async def send_post(client, callback_query):
    admin_id = callback_query.from_user.id
    session = post_sessions.get(admin_id)

    if not session:
        return await callback_query.answer("Session expired.", show_alert=True)

    channel_id = session["channel"]

    for msg in session["messages"]:
        try:
            if getattr(msg, "document", None) and msg.document.mime_type == "application/pdf":
                thumb_path = None
                if session.get("set_thumb"):
                    thumb_path = await tb.get_global_thumb()
                await safe_send(
                    client,
                    client.send_document,
                    chat_id=channel_id,
                    document=msg.document.file_id,
                    caption=msg.caption or "",
                    thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None
                )
            elif getattr(msg, "photo", None):
                await safe_send(client, client.send_photo, chat_id=channel_id, photo=msg.photo.file_id, caption=msg.caption or "")
            elif getattr(msg, "video", None):
                await safe_send(client, client.send_video, chat_id=channel_id, video=msg.video.file_id, caption=msg.caption or "")
            elif getattr(msg, "text", None):
                await safe_send(client, client.send_message, chat_id=channel_id, text=msg.text)
        except Exception as ex:
            print(f"[PostError] {ex}")

    await callback_query.message.edit_text("🎉 Post successfully published!")
    post_sessions.pop(admin_id, None)  # clear session
