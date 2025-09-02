import random
from pyrogram import Client, filters, enums
from pyrogram.errors import *
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import *
import asyncio
from Script import text
from .db import tb
from .fsub import get_fsub

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
            [InlineKeyboardButton('⇆ 𝖠𝖽𝖽 𝖬𝖾 𝖳𝗈 𝖸𝗈𝗎𝗋 𝖦𝗋𝗈𝗎𝗉 ⇆', url=f"https://telegram.me/QuickAcceptBot?startgroup=true&admin=invite_users")],
            [InlineKeyboardButton('ℹ️ 𝖠𝖻𝗈𝗎𝗍', callback_data='about'),
             InlineKeyboardButton('📚 𝖧𝖾𝗅𝗉', callback_data='help')],
            [InlineKeyboardButton('⇆ 𝖠𝖽𝖽 𝖬𝖾 𝖳𝗈 𝖸𝗈𝗎𝗋 𝖢𝗁𝖺𝗇𝗇𝖾𝗅 ⇆', url=f"https://telegram.me/QuickAcceptBot?startchannel=true&admin=invite_users")]
            ])
        )

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    reply = await message.reply(
        text=("❓ <b>𝘏𝘢𝘷𝘪𝘯𝘨 𝘛𝘳𝘰𝘶𝘣𝘭𝘦?</b>\n\n𝘐𝘧 𝘺𝘰𝘶'𝘳𝘦 𝘧𝘢𝘤𝘪𝘯𝘨 𝘢𝘯𝘺 𝘱𝘳𝘰𝘣𝘭𝘦𝘮 𝘸𝘩𝘪𝘭𝘦 𝘶𝘴𝘪𝘯𝘨 𝘵𝘩𝘦 𝘣𝘰𝘵 𝘰𝘳 𝘪𝘵𝘴 𝘤𝘰𝘮𝘮𝘢𝘯𝘥𝘴, 𝘱𝘭𝘦𝘢𝘴𝘦 𝘸𝘢𝘵𝘤𝘩 𝘵𝘩𝘦 𝘵𝘶𝘵𝘰𝘳𝘪𝘢𝘭 𝘷𝘪𝘥𝘦𝘰 𝘣𝘦𝘭𝘰𝘸.\n\n🎥 𝘛𝘩𝘦 𝘷𝘪𝘥𝘦𝘰 𝘸𝘪𝘭𝘭 𝘤𝘭𝘦𝘢𝘳𝘭𝘺 𝘦𝘹𝘱𝘭𝘢𝘪𝘯 𝘩𝘰𝘸 𝘵𝘰 𝘶𝘴𝘦 𝘦𝘢𝘤𝘩 𝘧𝘦𝘢𝘵𝘶𝘳𝘦 𝘸𝘪𝘵𝘩 𝘦𝘢𝘴𝘦.\n\n💖 𝘍𝘰𝘳 𝘮𝘰𝘳𝘦 𝘶𝘱𝘥𝘢𝘵𝘦𝘴 — <b><a href='https://techifybots.github.io/PayWeb/'>𝘚𝘶𝘱𝘱𝘰𝘳𝘵 𝘜𝘴.</a></b>"
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 𝘞𝘢𝘵𝘤𝘩 𝘛𝘶𝘵𝘰𝘳𝘪𝘢𝘭", url="https://youtu.be/_n3V0gFZMh8")]
        ])
    )
    await asyncio.sleep(300)
    await reply.delete()
    try:
        await message.delete()
    except:
        pass

@Client.on_message(filters.command('accept') & filters.private)
async def accept(client, message):
    show = await message.reply("**Please Wait.....**")
    user_data = await tb.get_session(message.from_user.id)
    if user_data is None:
        return await show.edit("**To accept join requests, please /login first.**")
    try:
        acc = Client("joinrequest", session_string=user_data, api_id=API_ID, api_hash=API_HASH)
        await acc.connect()
    except:
        return await show.edit("**Your login session has expired. Use /logout first, then /login again.**")
    await show.edit("**Forward a message from your Channel or Group (with forward tag).\n\nMake sure your logged-in account is an admin there with full rights.**")
    fwd_msg = await client.listen(message.chat.id)
    if fwd_msg.forward_from_chat and fwd_msg.forward_from_chat.type not in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
        chat_id = fwd_msg.forward_from_chat.id
        try:
            info = await acc.get_chat(chat_id)
        except:
            return await show.edit("**Error: Ensure your account is admin in this Channel/Group with required rights.**")
    else:
        return await message.reply("**Message not forwarded from a valid Channel/Group.**")
    await fwd_msg.delete()
    msg = await show.edit("**Accepting all join requests... Please wait.**")
    try:
        while True:
            await acc.approve_all_chat_join_requests(chat_id)
            await asyncio.sleep(1)
            join_requests = [req async for req in acc.get_chat_join_requests(chat_id)]
            if not join_requests:
                break
        await msg.edit("**✅ Successfully accepted all join requests.**")
    except Exception as e:
        await msg.edit(f"**An error occurred:** `{str(e)}`")

@Client.on_chat_join_request()
async def approve_new(client, m):
    if not NEW_REQ_MODE:
        return
    try:
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        try:
            await client.send_message(
                m.from_user.id,
                f"{m.from_user.mention},\n\n𝖸𝗈𝗎𝗋 𝖱𝖾𝗊𝗎𝗌𝗍 𝖳𝗈 𝖩𝗈𝗂𝗇 {m.chat.title} 𝖧𝖺𝗌 𝖡𝖾𝖾𝗇 𝖠𝖼𝖼𝖾𝗉𝗍𝖾𝖽."
            )
        except:
            pass
    except Exception as e:
        print(str(e))
        pass