import pyrogram
from pyrogram import Client, filters
from pyrogram.enums import ChatType


async def blacklist_filter_function(_, app, message):
    blacklist_users = app.get_config_parameter('blacklist_users')
    if message.from_user:
        user = message.from_user
        if user.username and user.username in blacklist_users:
            return True
        if user.id in blacklist_users:
            return True


    blacklist_sender_chats = app.get_config_parameter('blacklist_sender_chats')
    if message.sender_chat:
        user = message.sender_chat
        if user.username and user.username in blacklist_sender_chats:
            return True
        if user.id in blacklist_sender_chats:
            return True

    blacklist_chats = app.get_config_parameter('blacklist_chats')
    if message.chat:
        chat = message.chat
        if chat.username and chat.username in blacklist_chats:
            return True
        if chat.id in blacklist_chats:
            return True

        if chat.type == ChatType.CHANNEL and app.get_config_parameter('ignore_posts_in_channels'):
            return True

    return False


blacklist_filter = filters.create(blacklist_filter_function)


@Client.on_message(blacklist_filter, group=-2)
async def blacklist_middleware(_, msg):
    raise pyrogram.StopPropagation
