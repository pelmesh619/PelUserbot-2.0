import html
import math

from pyrogram import Client, filters

from utils import bot_utils

AMOUNT_MODULES_ON_PAGE = 5


@Client.on_message(filters.me & filters.command('handlers'))
async def handlers_handler(app, message):
    page = 0
    while True:
        handlers = list(app.get_all_handlers())

        if len(handlers) == 0:
            respond = app.get_core_string('handlers_list_empty')
            await message.edit_text(text=respond, disable_web_page_preview=True)
            return

        respond = [app.get_core_string(
            'handlers_list',
            count_handlers=len(handlers),
            form_handler=app.get_core_string_form('handler_form', len(handlers)))]
        respond += [app.get_core_string(
            'handlers_page_out_of',
            page=page + 1,
            amount_pages=math.ceil(len(handlers) / AMOUNT_MODULES_ON_PAGE))]
        respond += ['']

        for i in range(page * AMOUNT_MODULES_ON_PAGE, (page + 1) * AMOUNT_MODULES_ON_PAGE):
            if i >= len(handlers):
                break

            handler = handlers[i]
            module = app.get_module_by_handler(*handler)

            module_full_name = module.full_name() if module else None

            respond += [app.get_core_string(
                'handler_template'+('_in_module' if module_full_name else ''),
                name=handler[0].callback.__name__,
                group=handler[1],
                module_name=module_full_name,
            )]

        respond += ['']
        if 0 < page < math.ceil(len(handlers) / AMOUNT_MODULES_ON_PAGE) - 1:
            respond += [
                app.get_core_string(
                    'handlers_page_all_switches',
                    forward=html.escape('>'),
                    backward=html.escape('<')
                )
            ]
        elif not page > 0:
            respond += [app.get_core_string('handlers_page_forward_switch', forward=html.escape('>'))]
        elif not page < math.ceil(len(handlers) / AMOUNT_MODULES_ON_PAGE) - 1:
            respond += [app.get_core_string('handlers_page_backward_switch', backward=html.escape('<'))]

        respond = '\n'.join(respond)
        await message.edit_text(text=respond, disable_web_page_preview=True)

        answer = await bot_utils.wait_answer(
            message,
            filters.me & filters.text,
            possible_results=['<' if page > 0 else None, '>' if page < math.ceil(
                len(handlers) / AMOUNT_MODULES_ON_PAGE) - 1 else None],
            deleting_message_timeout=5
        )

        if answer.text == '<':
            page -= 1
        else:
            page += 1
