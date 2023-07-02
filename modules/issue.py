import re

from pyrogram import Client, filters
from pyrogram.enums import ChatType

from core import Module

module = Module(
    strings={
        'ru': {
            "issue_enter_your_issue": "Введите ваш вопрос/предложение (<code>/issue <предложение></code>) или "
                                      "ответьте вопросом/предложением на это сообщение, и я отправлю его разработчику🙂",
            "issue_form": "#issue <b>Вопрос/предложение</b>:\n\n"
                          "Пользователь: {user_mention} "
                          "(uid=<code>{user_id}</code>, lc=<code>'{language_code}'</code>)\n"
                          "Сообщение: (mid=<code>{message_id}</code>)\n\n{issue}",
            "issue_form_chat": "#issue <b>Вопрос/предложение</b>:\n\n"
                               "Пользователь: {user_mention} "
                               "(uid=<code>{user_id}</code>, lc=<code>'{language_code}'</code>)\n"
                               "Чат: {chat_title} (cid=<code>{chat_id}</code>)\n"
                               "Сообщение: (mid=<code>{message_id}</code>)\n\n{issue}",
            "issue_was_sent": "Ваш вопрос/предложение {attached}{issue}был отправлен👌",
            "with_attached_photo": "с прикрепленным фото",
            "with_attached_video": "с прикрепленным видео",
            "with_attached_animation": "с прикрепленной гифкой",
            "with_attached_document": "с прикрепленным файлом",
            "with_attached_sticker": "с прикрепленным стикером",
            "with_attached_voice": "с прикрепленным голосовым сообщением",
            "with_attached_video_note": "с прикрепленным видеосообщением",
            "with_attached_contact": "с прикрепленным контактом",
            "with_attached_location": "с прикрепленной локацией",
            "with_attached_venue": "с прикрепленным местоположением",
            "with_attached_poll": "с прикрепленным опросом",
            "with_attached_game": "с прикрепленной игрой",
            "attached_photo": "[прикрепленное фото]",
            "attached_video": "[прикрепленное видео]",
            "attached_animation": "[прикрепленная гифка]",
            "attached_document": "[прикрепленный файл]",
            "attached_sticker": "[прикрепленный стикер]",
            "attached_voice": "[прикрепленное голосовое сообщение]",
            "attached_video_note": "[прикрепленное видеосообщение]",
            "attached_contact": "[прикрепленный контакт]",
            "attached_location": "[прикрепленная локация]",
            "attached_venue": "[прикрепленное местоположение]",
            "attached_poll": "[прикрепленный опрос]",
            "attached_game": "[прикрепленная игра]",
            "invalid_data": "Неправильные данные",
            "issue_reply_chat": "{user}, вот ответ разработчика на ваш вопрос/предложение: {answer}",
            "issue_reply": "Хей, вот ответ разработчика на ваш вопрос/предложение: {answer}",
            "issue_was_replied": "Ответ на вопрос/предложение успешно отправлен",

        }
    },
    config={
        'owner_ids': [1134950789]
    }
)


async def is_owner(_, __, msg):
    return msg.from_user.id in module.get_config_parameter('owner_ids')


async def reply_from_bot(_, app, msg):
    if not msg.reply_to_message:
        return
    if not msg.reply_to_message.from_user:
        return
    if not msg.reply_to_message.from_user.id == app.me.id:
        return
    return True


reply_from_bot_filter = filters.create(reply_from_bot)


@Client.on_message(filters.command(['issue', 'question']))
async def issue_command(app, message):
    my_username = app.me.username or ""
    text = message.text or message.caption
    issue = re.sub(rf"^{message.command[0]}(?:@?{my_username})?\s?", "", text.html[1:], count=1, flags=re.IGNORECASE)
    if message.reply_to_message and not issue:
        issue = message.reply_to_message.text or message.reply_to_message.caption
        if issue:
            issue = issue.html

    attached_message = message.reply_to_message or message
    media_type = getattr(attached_message.media, 'value', None)
    attached_media = getattr(attached_message, media_type) if media_type else None

    if not (issue or (media_type and media_type != 'web_page')):
        await message.reply(message.get_string('issue_enter_your_issue'))

    else:
        user = message.from_user
        chat = message.chat
        sender_chat = message.sender_chat

        issue_form = message.get_string(
            'issue_form' + ('_chat' if message.chat.type != ChatType.PRIVATE else ''),
            issue=issue if issue else (
                message.get_string('attached_' + media_type) if media_type and media_type != 'web_page' else ''),
            chat_id=chat.id,
            chat_title=str(chat.title) + (f' ({chat.username})' if chat.username else ''),
            user_id=getattr(message.from_user or message.sender_chat, 'id', None),
            user_mention=user and user.mention or sender_chat and (
                    sender_chat.title + (f' ({sender_chat.username})' if sender_chat.username else '')),
            language_code=user.language_code,
            message_id=message.id

        )

        for chat in module.get_config_parameter('owner_ids'):
            try:
                if attached_media and media_type != 'web_page':
                    await attached_message.forward(chat)

                await app.send_message(chat, issue_form)
            except:
                print(chat, 'is invalid / issue')
                pass
        await message.reply(
            message.get_string(
                'issue_was_sent',
                issue=('\n\n' + issue + '\n\n') if issue else '',
                attached=(message.get_string(
                    'with_attached_' + media_type) + ' ') if media_type and media_type != 'web_page' else ''
            )
        )


@Client.on_message(reply_from_bot_filter & filters.reply_identify_string('issue_enter_your_issue'), group=1)
async def issue_reply(app, message):
    media_type = getattr(message.media, 'value', None)
    attached_media = getattr(message, media_type) if media_type else None

    issue = message.text or message.caption
    if issue:
        issue = issue.html

    user = message.from_user
    chat = message.chat
    sender_chat = message.sender_chat

    issue_form = message.get_string(
        'issue_form' + ('_chat' if message.chat.type != ChatType.PRIVATE else ''),
        issue=issue if issue else (
            message.get_string('attached_' + media_type) if media_type and media_type != 'web_page' else ''),
        chat_id=chat.id,
        chat_title=str(chat.title) + (f' ({chat.username})' if chat.username else ''),
        user_id=getattr(message.from_user or message.sender_chat, 'id', None),
        user_mention=user and user.mention or sender_chat and (
                sender_chat.title + (f' ({sender_chat.username})' if sender_chat.username else '')),
        language_code=user.language_code,
        message_id=message.id

    )

    for chat in module.get_config_parameter('owner_ids'):
        try:
            if attached_media and media_type != 'web_page':
                await message.forward(chat)

            await app.send_message(chat, issue_form)
        except:
            print(chat, 'is invalid / issue')
            pass
    await message.reply(
        message.get_string(
            'issue_was_sent',
            issue=('\n\n' + issue + '\n\n') if issue else '',
            attached=(message.get_string(
                'with_attached_' + media_type) + ' ') if media_type and media_type != 'web_page' else ''
        )
    )


@Client.on_message(
    reply_from_bot_filter &
    filters.reply_identify_string(['issue_form', 'issue_form_chat'], flags=re.S) &
    filters.create(is_owner),
    group=1
)
async def issue(app, message):
    reply_text = message.reply_to_message.text or message.reply_to_message.caption
    string_id = message.identified_string_id
    # print(message.match, message.match.groups())
    user_id = message.match.group(2)
    language_code = message.match.group(3).strip('\'')
    if language_code == 'None':
        language_code = app.lang_code

    if string_id.endswith('chat'):
        chat_id = message.match.group(5)
        message_id = message.match.group(6)
    else:
        chat_id = user_id
        message_id = message.match.group(4)

    if not (user_id.isdigit() and chat_id[1:].isdigit() and message_id.isdigit()):
        return await message.reply(message.get_string('invalid_data'))

    user_id = int(user_id)
    chat_id = int(chat_id)
    message_id = int(message_id)

    try:
        assert await app.get_messages(chat_id, message_id)
    except:
        message_id = None

    answer = message.text
    if answer:
        answer = answer.html

    if string_id.endswith('chat'):
        user = (await app.get_users(user_id)).mention

        await app.send_message(
            chat_id,
            message.get_string('issue_reply_chat', user=user, lang_code=language_code, answer=answer if answer else ''),
            reply_to_message_id=message_id,
        )

        if not answer:
            await message.copy(chat_id)

    else:
        await app.send_message(
            chat_id,
            message.get_string('issue_reply', lang_code=language_code, answer=answer if answer else ''),
            reply_to_message_id=message_id,
        )

        if not answer:
            await message.copy(chat_id)

    await message.reply(message.get_string('issue_was_replied'))
