from pyrogram import Client, filters, enums
from pyrogram.errors import *
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
import asyncio
import random
from Script import text
from TechifyBots.db import tb  # Techifybots instance
from TechifyBots.fsub import get_fsub
from pyrogram.errors import FloodWait

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


# --------------- /start command ---------------
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
    if IS_FSUB and not await get_fsub(client, message): return
    await message.reply_photo(
        photo=random.choice(PICS),
        caption=text.START.format(message.from_user.mention),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('⇆ 𝖠𝖽𝖽 𝖬𝖾 𝖳𝗈 𝖸𝗈𝗎𝗋 𝖦𝗋𝗈𝗎𝗉 ⇆', url=f"https://telegram.me/NG_file_rename_bot?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ℹ️ 𝖠𝖻𝗈𝗎𝗍', callback_data='about'),
             InlineKeyboardButton('📚 𝖧𝖾𝗅𝗉', callback_data='help')],
            [InlineKeyboardButton('⇆ 𝖠𝖽𝖽 𝖬𝖾 𝖳𝗈 𝖸𝗈𝗎𝗋 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 ⇆', url=f"https://telegram.me/NG_file_rename_bot?startchannel=true&admin=invite_users")]
        ])
    )


# --------------- /help command ---------------
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    reply = await message.reply(
        text=("❓ <b>𝘏𝘢𝘷𝘪𝘯𝘨 𝘛𝘳𝘰𝘶𝘣𝘭𝘦?</b>\n\n𝘐𝘧 𝘺𝘰𝘶'𝘳𝘦 𝘧𝘢𝘤𝘪𝘯𝘨 𝘢𝘯𝘺 𝘱𝘳𝘰𝘣𝘭𝘦𝘮 𝘸𝘩𝘪𝘭𝘦 𝘶𝘴𝘪𝘯𝘨 𝘵𝘩𝘦 𝘣𝘰𝘵 𝘰𝘳 𝘪𝘵𝘴 𝘤𝘰𝘮𝘮𝘢𝘯𝘥𝘴, 𝘱𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘵𝘤𝘩 𝘵𝘩𝘦 𝘵𝘶𝘵𝘰𝘳𝘪𝘢𝘭 𝘷𝘪𝘥𝘦𝘰 𝘣𝘦𝘭𝘰𝘸.\n\n🎥 𝘛𝘩𝘦 𝘷𝘪𝘥𝘦𝘰 𝘸𝘪𝘭𝘭 𝘤𝘭𝘦𝘢𝘳𝘭𝘺 𝘦𝘹𝘱𝘭𝘢𝘪𝘯 𝘩𝘰𝘸 𝘵𝘰 𝘶𝘴𝘦 𝘦𝘢𝘤𝘩 𝘧𝘦𝘢𝘵𝘶𝘳𝘦 𝘸𝘪𝘵𝘩 𝘦𝘢𝘴𝘦.\n\n💖 𝘍𝘰𝘳 𝘮𝘰𝘳𝘦 𝘶𝘱𝘥𝘢𝘵𝘦𝘴 — <b><a href='https://techifybots.github.io/PayWeb/'>𝘚𝘶𝘱𝘱𝘰𝘳𝘵 𝘜𝘴.</a></b>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 𝘞𝘢𝘵𝘤𝘩 𝘛𝘶𝘵𝘰𝘳𝘪𝘢𝘭", url="https://youtube.com/@CodeByJerry")]
        ])
    )
    await asyncio.sleep(300)
    await reply.delete()
    try:
        await message.delete()
    except:
        pass


# --------------- /accept command (simplified) ---------------
@Client.on_message(filters.command('accept') & filters.private)
async def accept(client, message: Message):
    # Just inform the admin that auto-approve is active
    await message.reply("✅ Auto-approve is active. All new join requests will be accepted automatically.")

# --------------- Auto-approve new requests ---------------
@Client.on_chat_join_request()
async def approve_new(client, m):
    try:
        # Approve every join request automatically
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        try:
            # Optional: notify the user
            await client.send_message(
                m.from_user.id,
                f"{m.from_user.mention},\n\nYour request to join {m.chat.title} has been approved ✅"
            )
        except:
            pass
    except Exception as e:
        print(f"[AutoApproveError] {e}")
        pass

# --------------- /addchannel command ---------------
@Client.on_message(filters.command("addchannel") & filters.user([ADMIN]))
async def add_channel_cmd(client: Client, message: Message):
    # Ask admin to forward a message from the channel
    prompt = await message.reply(
        "📌 Forward a message from the channel you want to register"
    )

    try:
        fwd_msg = await client.listen(message.chat.id)  # wait for the forwarded message
    except Exception as e:
        return await prompt.edit(f"⚠️ Error: {str(e)}")

    if fwd_msg.forward_from_chat and fwd_msg.forward_from_chat.type == enums.ChatType.CHANNEL:
        chat_id = fwd_msg.forward_from_chat.id
        title = fwd_msg.forward_from_chat.title

        # Save to DB
        await tb.add_channel(chat_id, title)
        await prompt.edit(f"✅ Channel **{title}** registered successfully!")
    else:
        await prompt.edit("⚠️ Forwarded message is not from a valid channel.")


# --------------- /post command ---------------
@Client.on_message(filters.command("post") & filters.user([ADMIN]))
async def start_post(client: Client, message: Message):
    admin_id = message.from_user.id

    # Fetch allowed channels from DB
    channels = await tb.get_channels()
    if not channels:
        return await message.reply("⚠️ No channels registered. Please add channels first by /addchannel.")

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
