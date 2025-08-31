import random
import asyncio
import os
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import ADMIN, PICS, LOG_CHANNEL
from Script import text
from .db import tb
from .fsub import get_fsub

# Temporary local thumbnail storage
user_thumbs = {}

# ------------------ ADMIN CHECK ------------------
async def is_admin(client: Client, message: Message) -> bool:
    user_id = message.from_user.id
    if user_id == ADMIN:
        return True
    try:
        member = await client.get_chat_member(message.chat.id, user_id)
        return member.status in [enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR]
    except Exception:
        return False

# ------------------ START ------------------
@Client.on_message(filters.command("start"))
async def start_cmd(client, message):
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
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('⇆ Add me to your group ⇆', url=f"https://t.me/QuickAcceptBot?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ℹ️ About', callback_data='about'),
             InlineKeyboardButton('📚 Help', callback_data='help')],
            [InlineKeyboardButton('⇆ Add me to your channel ⇆', url=f"https://t.me/QuickAcceptBot?startchannel=true&admin=invite_users")]
        ])
    )

# ------------------ HELP ------------------
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    reply = await message.reply(
        text=("❓ <b>Having Trouble?</b>\n\n"
              "Watch the tutorial video to understand features clearly."),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Watch Tutorial", url="https://youtu.be/_n3V0gFZMh8")]
        ])
    )
    await asyncio.sleep(300)
    await reply.delete()
    try:
        await message.delete()
    except:
        pass

# ------------------ SET THUMB ------------------
@Client.on_message(filters.command("setthumb") & filters.reply)
async def set_thumb(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("⚠️ Only admins can use this command")
    if not message.reply_to_message.photo:
        return await message.reply_text("Reply to a JPG photo with /setthumb to save it")

    photo = message.reply_to_message.photo
    if photo.file_size > 200 * 1024:  # 200kb check
        return await message.reply_text("⚠️ Thumbnail must be less than 200KB")

    file_id = photo.file_id
    try:
        await tb.save_thumb(message.from_user.id, file_id)
        await message.reply_text("✅ Thumbnail saved to database")
    except:
        path = f"thumb_{message.from_user.id}.jpg"
        await message.reply_to_message.download(file_name=path)
        user_thumbs[message.from_user.id] = path
        await message.reply_text("✅ Thumbnail saved locally")

# ------------------ CLEAR THUMB ------------------
@Client.on_message(filters.command("clearthumb"))
async def clear_thumb(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("⚠️ Only admins can use this command")
    user_id = message.from_user.id
    try:
        await tb.clear_thumb(user_id)
        await message.reply_text("🗑️ Thumbnail cleared from database")
    except:
        if user_id in user_thumbs:
            try:
                os.remove(user_thumbs[user_id])
            except:
                pass
            user_thumbs.pop(user_id, None)
            await message.reply_text("🗑️ Local thumbnail cleared")
        else:
            await message.reply_text("No thumbnail found")

# ------------------ POST ------------------
@Client.on_message(filters.command("post"))
async def post_handler(client, message: Message):
    if not await is_admin(client, message):
        return await message.reply_text("⚠️ Only admins can use this command")

    if not message.reply_to_message:
        return await message.reply_text(
            "Usage:\n\nReply to a <b>PDF</b> or <b>Text</b> with:\n"
            "`/post <channel_id>`\n\nExample:\n`/post -1001234567890`",
            parse_mode="html"
        )

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.reply_text("⚠️ Provide channel ID\nExample: `/post -1001234567890`")

    channel_id = args[1]
    user_id = message.from_user.id

    # get thumb
    thumb = None
    try:
        thumb = await tb.get_thumb(user_id)
    except:
        thumb = None
    if not thumb and user_id in user_thumbs:
        thumb = InputFile(user_thumbs[user_id])

    reply_msg = message.reply_to_message
    try:
        if reply_msg.document and reply_msg.document.mime_type == "application/pdf":
            kwargs = {
                "chat_id": channel_id,
                "document": reply_msg.document.file_id,
                "caption": reply_msg.caption or "📄 PDF File"
            }
            if thumb:
                kwargs["thumb"] = thumb
            await client.send_document(**kwargs)

        elif reply_msg.text:
            await client.send_message(chat_id=channel_id, text=reply_msg.text)

        else:
            return await message.reply_text("⚠️ Reply must be PDF or text")

        await message.reply_text("✅ Posted successfully!")

    except Exception as e:
        await message.reply_text(f"❌ Failed to post: {e}")
