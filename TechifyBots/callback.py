from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from Script import text
from config import ADMIN
from TechifyBots.db import tb
import os

THUMB_PATH = os.path.join("assets", "thumb.jpg")


@Client.on_callback_query()
async def callback_query_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    # -------------------- MAIN MENU --------------------
    if data == "start":
        await query.message.edit_caption(
            caption=text.START.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('⇆ Add me to your group ⇆',
                                      url="https://telegram.me/QuickAcceptBot?startgroup=true&admin=invite_users")],
                [InlineKeyboardButton('ℹ️ About', callback_data='about'),
                 InlineKeyboardButton('📚 Help', callback_data='help')],
                [InlineKeyboardButton('⇆ Add me to your channel ⇆',
                                      url="https://telegram.me/QuickAcceptBot?startchannel=true&admin=invite_users")]
            ])
        )

    elif data == "help":
        await query.message.edit_caption(
            caption=text.HELP.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('📢 Updates', url='https://telegram.me/NG_botz'),
                 InlineKeyboardButton('💬 Support', url='https://t.me/NG_bot_support')],
                [InlineKeyboardButton('↩️ Back', callback_data="start"),
                 InlineKeyboardButton('❌ Close', callback_data="close")]
            ])
        )

    elif data == "about":
        await query.message.edit_caption(
            caption=text.ABOUT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('👨‍💻 Developer', user_id=int(ADMIN))],
                [InlineKeyboardButton("↩️ Back", callback_data="start"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    elif data == "close":
        await query.message.delete()

    # -------------------- POST MENU --------------------
    elif data.startswith("post_channel:"):
        channel_id = int(data.split(":")[1])
        session = await tb.get_session(user_id)
        if session:
            session["channel_id"] = channel_id
        else:
            session = {"channel_id": channel_id, "messages": []}
        await tb.set_session(user_id, session)

        await query.message.edit_text(
            "Send me one or multiple messages you want to include in the post. It can be anything — text, photo, video, even a sticker.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")]
            ])
        )

    elif data == "add_more":
        await query.message.edit_text(
            "Okay, send me more messages to add in this post.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Continue ➡️", callback_data="continue_post")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")]
            ])
        )

    elif data == "continue_post":
        session = await tb.get_session(user_id)
        if not session:
            return await query.message.edit_text("⚠️ Session expired. Please restart with /post.")
        if not session.get("messages"):
            return await query.message.edit_text("⚠️ No messages saved yet. Please send something first.")

        has_pdf = any(getattr(msg, "document", None) and msg.document.mime_type == "application/pdf" for msg in session.get("messages", []))

        if has_pdf:
            await query.message.edit_text(
                "This post contains PDF(s). Do you want to set the global thumbnail?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📎 Set Thumb", callback_data="set_thumb")],
                    [InlineKeyboardButton("➡️ Continue", callback_data="finalize_post")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="add_more")]
                ])
            )
        else:
            await query.message.edit_text(
                "Post is ready to post.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Send", callback_data="send_post")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="add_more")]
                ])
            )

    elif data == "set_thumb":
        session = await tb.get_session(user_id)
        if not session:
            return await query.message.edit_text("⚠️ Session expired. Please restart with /post.")

        session["set_thumb"] = True
        await tb.set_session(user_id, session)

        await query.message.edit_text(
            "✅ Global thumbnail has been applied to PDFs.\n\nNow confirm:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Send", callback_data="send_post")],
                [InlineKeyboardButton("⬅️ Back", callback_data="continue_post")]
            ])
        )

    elif data == "finalize_post":
        await query.message.edit_text(
            "Post is ready to post.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Send", callback_data="send_post")],
                [InlineKeyboardButton("⬅️ Back", callback_data="add_more")]
            ])
        )

    elif data == "send_post":
        session = await tb.get_session(user_id)
        if not session:
            return await query.message.edit_text("⚠️ Session expired. Please restart with /post.")

        channel_id = session.get("channel_id")
        messages = session.get("messages", [])

        if not channel_id:
            return await query.message.edit_text("⚠️ No channel selected. Please restart with /post.")
        if not messages:
            return await query.message.edit_text("⚠️ No messages found. Please restart with /post.")

        for msg in messages:
            try:
                if getattr(msg, "document", None) and msg.document.mime_type == "application/pdf" and session.get("set_thumb"):
                    thumb_path = await tb.get_global_thumb()
                    await msg.copy(chat_id=channel_id, caption=msg.caption, thumb=thumb_path if thumb_path and os.path.exists(thumb_path) else None)
                else:
                    await msg.copy(chat_id=channel_id)
            except Exception as e:
                print("Error while sending message:", e)
                await query.message.edit_text(f"⚠️ Failed to send a message: {e}")
                return

        await query.message.edit_text("✅ Post has been sent successfully!")
        await tb.set_session(user_id, None)

    elif data == "cancel_post":
        await tb.set_session(user_id, None)
        await query.message.edit_text("❌ Post cancelled.")
