from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from Script import text
from config import ADMIN


@Client.on_callback_query()
async def callback_query_handler(client, query: CallbackQuery):
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
