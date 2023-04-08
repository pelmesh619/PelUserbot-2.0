import asyncio

from pyrogram import Client, filters

from utils import bot_utils


async def wait_answer_handler_filter(_, app, msg):
    """string_id=wait_answer_filter_description

    Filters message that is reply to the message
    that waiting answer by utils.wait_answer

    :param _: self
    :param app: core.Peluserbot
    :param msg: pyrogram.types.Message
    :return: bool
    """

    reply = msg.reply_to_message
    if not reply:
        return

    key = (getattr(reply.chat, 'id', None), reply.id)
    text = msg.text or msg.caption
    if key not in app.answers:
        return

    if app.answers[key].result is None:
        if app.answers[key].possible_results and text:
            if text not in app.answers[key].possible_results:
                return False

        filters = app.answers[key].filters

        if not await bot_utils.call_filters(filters, app, msg):
            return

        if app.answers[key].is_multiple:
            app.answers[key].results.append(msg)
            app.answers[key].queue.insert(0, msg)
        else:
            app.answers[key].result = msg

        msg.deleting_message_timeout = app.answers[key].deleting_message_timeout

        return True


@Client.on_message(filters.reply &
                   filters.create(wait_answer_handler_filter), -1)
async def wait_answer_handler(_, msg):
    if msg.deleting_message_timeout >= 0:
        await asyncio.sleep(msg.deleting_message_timeout)
        await msg.delete()
