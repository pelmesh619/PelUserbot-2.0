import asyncio

from pyrogram import filters, Client


@Client.on_message(filters.me & filters.command(['blacklist', 'sblacklist']), group=-3)
async def blacklist_handler(app, message):
    is_silent = message.command[0].startswith('s')
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.from_user:
            user = reply.from_user
            blacklist_users = app.get_config_parameter('blacklist_users')
            was_removed = False

            if user.id in blacklist_users:
                was_removed = True
                blacklist_users.remove(user.id)
            if user.username and user.username in blacklist_users:
                was_removed = True
                blacklist_users.remove(user.username)

            if not was_removed:
                blacklist_users.append(user.id)

            app.set_config_parameter('blacklist_users', blacklist_users)
            text = message.get_string(
                'blacklist_user_was_removed' if was_removed else 'blacklist_user_was_added',
                mention=user.mention
            )
            if not is_silent:
                await message.edit(text, disable_web_page_preview=True)
            else:
                await message.delete()
                await app.send_message('me', text, disable_web_page_preview=True)
            return

        if reply.sender_chat:
            sender_chat = reply.sender_chat
            blacklist_sender_chats = app.get_config_parameter('blacklist_sender_chats')
            was_removed = False

            if sender_chat.id in blacklist_sender_chats:
                was_removed = True
                blacklist_sender_chats.remove(sender_chat.id)
            if sender_chat.username and sender_chat.username in blacklist_sender_chats:
                was_removed = True
                blacklist_sender_chats.remove(sender_chat.username)

            if not was_removed:
                blacklist_sender_chats.append(sender_chat.id)

            app.set_config_parameter('blacklist_sender_chats', blacklist_sender_chats)
            title = sender_chat.title or ' '.join(filter(lambda x: x, [sender_chat.first_name, sender_chat.last_name]))
            text = message.get_string(
                'blacklist_sender_chat_was_removed' if was_removed else 'blacklist_sender_chat_was_added',
                mention=f'<i><a href="t.me/{sender_chat.username}">{title}</a></i>'
                if sender_chat.username else f'<i>{title}</i>'
            )
            if not is_silent:
                await message.edit(text, disable_web_page_preview=True)
            else:
                await message.delete()
                await app.send_message('me', text, disable_web_page_preview=True)
            return

    chat = message.chat
    blacklist_chats = app.get_config_parameter('blacklist_chats')
    was_removed = False

    if chat.id in blacklist_chats:
        was_removed = True
        blacklist_chats.remove(chat.id)
    if chat.username and chat.username in blacklist_chats:
        was_removed = True
        blacklist_chats.remove(chat.username)

    if not was_removed:
        blacklist_chats.append(chat.id)

    app.set_config_parameter('blacklist_chats', blacklist_chats)
    title = chat.title or ' '.join(filter(lambda x: x, [chat.first_name, chat.last_name]))
    text = message.get_string(
        'blacklist_chat_was_removed' if was_removed else 'blacklist_chat_was_added',
        mention=f'<i><a href="t.me/{chat.username}">{title}</a></i>'
        if chat.username else f'<i>{title}</i>'
    )
    if not is_silent:
        await message.edit(text, disable_web_page_preview=True)
    else:
        await message.delete()
        await app.send_message('me', text, disable_web_page_preview=True)


