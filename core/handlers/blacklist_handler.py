from pyrogram import filters, Client


@Client.on_message(filters.me & filters.command(['blacklist', 'sblacklist', 'blacklist\?', 'sblacklist\?']), group=-3)
async def blacklist_handler(app, message):
    is_silent = message.command[0].startswith('s')
    is_asking = message.command[0].endswith('?')

    was_removed = False
    blacklist_items: list

    scope = 'chat'
    item = message.chat
    name_view = f'<i><a href="t.me/{item.username}">{item.title}</a></i>' \
        if item.username else f'<i>{item.title}</i>'
    if message.reply_to_message:
        reply = message.reply_to_message
        if reply.from_user:
            scope = 'user'
            item = reply.from_user
            name_view = item.mention
        elif reply.sender_chat:
            scope = 'sender_chat'
            item = reply.sender_chat
            name_view = f'<i><a href="t.me/{item.username}">{item.title}</a></i>' \
                if item.username else f'<i>{item.title}</i>'

    blacklist_items = app.get_config_parameter(f'blacklist_{scope}s')

    if is_asking:
        answer = item.id in blacklist_items or item.username and item.username in blacklist_items
        text = message.get_string(
            'blacklist_{}_is{}_in_blacklist'.format(scope, '' if not answer else '_not'),
            mention=name_view
        )
    else:
        if item.id in blacklist_items:
            was_removed = True
            blacklist_items.remove(item.id)
        if item.username and item.username in blacklist_items:
            was_removed = True
            blacklist_items.remove(item.username)

        if not was_removed:
            blacklist_items.append(item.id)

        app.set_config_parameter(f'blacklist_{scope}s', blacklist_items)
        text = message.get_string(
            f'blacklist_{scope}_was_removed' if was_removed else f'blacklist_{scope}_was_added',
            mention=name_view
        )
    if not is_silent:
        await message.edit(text, disable_web_page_preview=True)
    else:
        await message.delete()
        await app.send_message('me', text, disable_web_page_preview=True)


