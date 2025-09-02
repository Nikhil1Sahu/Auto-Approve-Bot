from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from Script import text
from config import ADMIN
from TechifyBots.db import tb
  # our Techifybots instance


@Client.on_callback_query()
async def callback_query_handler(client, query: CallbackQuery):
    # -------------------- MAIN MENU --------------------
    if query.data == "start":
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

    elif query.data == "help":
        await query.message.edit_caption(
            caption=text.HELP.format(query.from_user.mention),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('📢 Updates', url='https://telegram.me/NG_botz'),
                 InlineKeyboardButton('💬 Support', url='https://t.me/NG_bot_support')],
                [InlineKeyboardButton('↩️ Back', callback_data="start"),
                 InlineKeyboardButton('❌ Close', callback_data="close")]
            ])
        )

    elif query.data == "about":
        await query.message.edit_caption(
            caption=text.ABOUT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton('👨‍💻 Developer', user_id=int(ADMIN))],
                [InlineKeyboardButton("↩️ Back", callback_data="start"),
                 InlineKeyboardButton("❌ Close", callback_data="close")]
            ])
        )

    elif query.data == "close":
        try:
            await query.message.delete()
        except:
            pass

    # -------------------- THUMBNAIL MANAGEMENT --------------------
    elif query.data == "thumb:view":
        thumb = await tb.get_thumb(query.from_user.id)
        if thumb:
            await query.message.reply_photo(thumb, caption="Here’s your saved thumbnail ✅")
        else:
            await query.answer("You don’t have a saved thumbnail", show_alert=True)

    elif query.data == "clearthumb:ask":
        await query.message.edit_caption(
            "⚠️ Are you sure you want to clear your saved thumbnail?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Yes, clear", callback_data="clearthumb:confirm")],
                [InlineKeyboardButton("❌ Cancel", callback_data="start")]
            ])
        )

    elif query.data == "clearthumb:confirm":
        success = await tb.clear_thumb(query.from_user.id)
        if success:
            await query.message.edit_caption("🗑️ Thumbnail cleared successfully!")
        else:
            await query.message.edit_caption("❌ No thumbnail found to clear.")

    # -------------------- POST BUILDER --------------------
    elif query.data == "post:add":
        await query.message.edit_caption(
            "📌 Send me the text you want in your post",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="close")]
            ])
        )
        tb.cache[query.from_user.id]["mode"] = "post_text"

    elif query.data == "post:continue":
        await query.message.edit_caption(
            "Now send an image (or skip)",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏭️ Skip Image", callback_data="post:skip_image")],
                [InlineKeyboardButton("❌ Cancel", callback_data="close")]
            ])
        )
        tb.cache[query.from_user.id]["mode"] = "post_image"

    elif query.data == "post:skip_image":
        await query.message.edit_caption(
            "Choose a thumbnail option 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌆 Use Saved Thumbnail", callback_data="post:thumb:saved")],
                [InlineKeyboardButton("🖼️ Upload New Thumbnail", callback_data="post:thumb:new")],
                [InlineKeyboardButton("❌ No Thumbnail", callback_data="post:thumb:none")]
            ])
        )

    elif query.data == "post:thumb:saved":
        thumb = await tb.get_thumb(query.from_user.id)
        if thumb:
            tb.cache[query.from_user.id]["thumb"] = thumb
            await query.message.edit_caption("✅ Saved thumbnail applied. Finalizing post...")
        else:
            await query.answer("No saved thumbnail found", show_alert=True)

    elif query.data == "post:thumb:new":
        await query.message.edit_caption(
            "📤 Send me a new thumbnail",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="close")]
            ])
        )
        tb.cache[query.from_user.id]["mode"] = "post_new_thumb"

    elif query.data == "post:thumb:none":
        tb.cache[query.from_user.id]["thumb"] = None
        await query.message.edit_caption("✅ No thumbnail selected. Finalizing post...")
