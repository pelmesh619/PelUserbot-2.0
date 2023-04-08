import asyncio
import io
import re
import time
import sys
import html
import logging
import traceback

import pyrogram.enums
from pyrogram import Client, filters
from core import Module, Author

import utils

log = logging.getLogger(__name__)

module = Module(
    name='string_id=pyexec_module_name',
    version='v1.0.0',
    authors=Author('pelmeshke', telegram_username='@pelmeshke'),
    description='string_id=description',
    changelog={},
    strings={
        'ru': {
            'pyexec_module_name': 'Исполнитель Pyexec',
            'description': 'Исполняет код на языке Python. Поддерживает вывод и полную информацию о ошибке',
            'code': '<b>Код</b>:\n<pre>{code}</pre>',
            'output': '<b>Вывод</b>:\n<code>{output}</code>',
            'no_args': '<b>Введите в команду код или ответьте на сообщение с кодом, чтобы его выполнить</b>',
            'return': '<b>Возвращено</b>: <code>{result}</code>',
            'error': '<b>Возникла ошибка</b>:\n<code>{error}</code>',
            'interpretation_error': '<b>Возникла ошибка интерпретации</b>:\n<code>{error}</code>',
            'time_spent': '<b>Потрачено времени</b>: {delta} с',
            'time_spent_without_input': '<b>Потрачено времени без взятия ввода</b>: {delta} с',
            'waiting_input': 'Ожидание ввода...',
            'program_needs_input': 'Программе нужен ввод (ответьте на это сообщение)\n\n<code>{prompt}</code>',
            'code_edited_filter': 'с измененным кодом внутри старого сообщения',
            'define_right_message_docs': 'являющиеся ответом на сообщение, ждущее ввод',
            # TODO docs for handlers
        },
        'en': {
            'code': '<b>Code</b>:\n<pre>{code}</pre>',
            'output': '<b>Output</b>:\n<code>{output}</code>',
            'no_args': '<b>Enter in command code or reply command to message to execute Python code</b>',
            'return': '<b>Returned</b>: <code>{result}</code>',
            'error': '<b>Error raised</b>:\n<code>{error}</code>',
            'time_spent': '<b>Time spent</b>: {delta} sec',
            'time_spent_without_input': '<b>Time spent without getting input</b>: {delta} sec',
            'waiting_input': 'Waiting user\'s input...',
            'program_needs_input': 'Program needs input (reply to this message)\n\n<code>{prompt}</code>',
        },
        'ge': {
            'code': '<b>Code</b>:\n<pre>{code}</pre>',
            'output': '<b>Ausgabe</b>:\n<code>{output}</code>',

        }

    },
)

_waiting_input_list = {}


class Console:
    def __init__(self, message=None, respond=''):
        self.file = ''
        self.message = message
        self.respond = respond
        self.getting_input_time = 0

    @staticmethod
    def write(str_, *_, **__):
        print(str_, end='', file=sys.__stdout__)
        # print__(str_, end='')

    def print(self, *args, sep=' ', end='\n'):
        print(*args, sep=sep, end=end, file=sys.__stdout__)
        self.file += sep.join([str(i) for i in args]) + end

    async def input(self, prompt='', *args, **kwargs):
        self.print(prompt, end='')

        current_time = time.time()
        try:
            if self.file:
                self.respond += '\n\n' + module.get_string('output', output=html.escape(self.file))
            await self.message.edit(self.respond + '\n\n' + module.get_string('waiting_input'))
        except Exception:
            pass

        input_respond = module.get_string('program_needs_input', prompt=prompt)
        input_message = await self.message.reply(input_respond, pyrogram.enums.ParseMode.HTML)
        key = input_message.chat.id, input_message.id
        _waiting_input_list[key] = None

        while _waiting_input_list[key] is None:
            await asyncio.sleep(0.1)
        input_value = _waiting_input_list[key]
        del _waiting_input_list[key]

        respond = re.sub(
            '\n\n' + re.escape(module.get_string('output', output='[specsimb]')).replace('\\[specsimb\\]', '(.*\n*)*'),
            '', self.respond)
        if not self.file:
            respond += '\n\n' + module.get_string('output', output=html.escape(self.file + input_value))
        self.print(input_value)
        try:
            await self.message.edit(respond + '\n\n' + module.get_string('waiting_input'))
        except Exception:
            pass

        await input_message.edit(input_respond + f'<i>{input_value}</i>', pyrogram.enums.ParseMode.HTML)

        delta = time.time() - current_time
        self.getting_input_time += delta

        return input_value


class ErrorConsole(io.StringIO):
    def __init__(self):
        super().__init__()
        self.file = ''

    def write(self, str_, *_, **__):
        self.file += str_
        print(str_, end='')


class Result:
    def __init__(
            self,
            console,
            returned=None,
            was_return=False,
            executing_time=0.0,
            error=None,
            error_console=None,
            interpretation_error=None
    ):
        self.console = console
        self.returned = returned
        self.executing_time = executing_time
        self.was_return = was_return
        self.error = error
        self.error_console = error_console
        self.interpretation_error = interpretation_error


def add_to_global(func):
    globals()[func.__name__] = func
    return func


async def asyncexec(code, **kwargs):
    code = f"async def __ex():\n    " + code.replace("\n", "\n    ")
    code = code.replace('input(', 'await input(')

    return_match = re.search(r'(\n( {4}|\t))([^ \t][^;\n]*; ?)*(return ?[^;\n]*)$', code)
    return_code = ''
    if not return_match and re.search(r'(\n( {4}|\t))[^ ].*$', code):
        return_code = re.sub(r'(\n( {4}|\t))(([^ \t\n;]*; *)*)(.+)$', '\g<1>\g<3>return \g<5>', code)

    message = kwargs.get('message')
    respond = kwargs.get('respond', '')
    console = Console(message, respond)
    error_console = ErrorConsole()

    global_vars = globals().copy()
    global_vars['print'] = console.print
    global_vars['input'] = console.input
    global_vars['global_'] = add_to_global
    global_vars.update(kwargs)

    is_executed = False
    if return_code:
        try:
            exec(return_code, global_vars)
            print(return_code, file=sys.__stdout__)
        except Exception:
            pass
        else:
            is_executed = True
    if not is_executed:
        try:
            exec(code, global_vars)
            print(code, file=sys.__stdout__)
        except Exception:
            error = sys.exc_info()
            traceback.print_exception(*error, file=error_console)
            result = Result(console, interpretation_error=error, error_console=error_console)
            return result

    current_time = time.time()
    try:
        returned = await global_vars["__ex"]()
        error = None
    except Exception:
        error = sys.exc_info()
        returned = None

    executing_time = time.time() - current_time
    if error is not None:
        traceback.print_exception(*error, file=error_console)
    result = Result(console, returned, bool(return_match), executing_time, error, error_console)

    return result


def kwargs_to_str(dict_, **kwargs):
    args = []
    for i in kwargs:
        dict_[i] = kwargs[i]
    for i in dict_:
        args.append(f'{i}={i}')

    return ', '.join(args)

# TODO fix this
def edit_code_filter(_, __, message):
    regex = re.escape(module.get_string('code', code='[specsimb]')).replace('\\[specsimb\\]', '(.*?)')
    possible_results = [
        '(' + '\n*' + re.escape(module.get_string('output', output='[specsimb]')).replace('\\[specsimb\\]',
                                                                                          '(.*)') + ')',
        '(' + '\n*' + re.escape(module.get_string('return', result='[specsimb]')).replace('\\[specsimb\\]',
                                                                                          '(.*)') + ')',
        '(' + '\n*' + re.escape(module.get_string('error', error='[specsimb]')).replace('\\[specsimb\\]', '(.*)') + ')',
        '(' + '\n*' + re.escape(module.get_string('interpretation_error', error='[specsimb]')).replace('\\[specsimb\\]',
                                                                                                       '(.*)') + ')',
        '(' + '\n*' + re.escape(module.get_string('time_spent', delta='[specsimb]')).replace('\\[specsimb\\]',
                                                                                             '(.*)') + ')',
    ]
    regex += '(' + '|'.join(possible_results) + ')'
    regex = regex.replace('\\\n', '\n').replace('\\ ', ' ')
    match = re.search(utils.remove_html_tags(regex), message.text, re.S)

    if match:
        script = match.group(1)

        if not script:
            return

        message.script = script
        return True


code_edited_filter = filters.create(
    edit_code_filter,
    __doc__='string_id=code_edited_filter'
)


#@Client.on_edited_message(filters.me & code_edited_filter)
@Client.on_message(filters.me & filters.command('exec'))
async def execute_handler(peluserbot, message):
    script = getattr(message, 'script', None) or ' '.join(message.text.split(' ')[1:])
    exec_msg = message

    if not script:
        if not message.reply_to_message:
            await message.edit_text(module.get_string('no_args'))
            return

        exec_msg = message.reply_to_message
        script = utils.get_message_entity(exec_msg, 'pre')
        print(script, utils.get_message_entity(exec_msg, 'pre'))
        if not script:
            script = utils.get_message_entity(exec_msg, 'code')
        if not script:
            script = exec_msg.text

    script = script.strip('\n')

    respond = module.get_string('code', code=html.escape(script))

    await message.edit_text(respond, parse_mode=pyrogram.enums.ParseMode.HTML)

    reply = (await peluserbot.get_messages(exec_msg.chat.id, exec_msg.id, replies=2)).reply_to_message

    kwargs = {
        'peluserbot': peluserbot,
        'message': exec_msg,
        'respond': respond,
        'app': peluserbot,
        'msg': exec_msg,
        'from_user': exec_msg.from_user,
        'chat': exec_msg.chat,
        'reply': reply,
        'reply_user': getattr(reply, 'from_user', None),
        '__message__': message,
    }

    result = await asyncexec(script, **kwargs)
    executing_time = result.executing_time
    output = result.console.file.strip('\n')
    if result.interpretation_error:
        exception_frames = reformat_exception_frames(result.error_console.file, script)
        respond += '\n\n' + module.get_string('interpretation_error', error=html.escape(exception_frames))
    else:

        if output:
            print(repr(output))
            respond += '\n\n' + module.get_string('output', output=html.escape(output))
        if result.error:
            exception_frames = reformat_exception_frames(result.error_console.file, script)
            print(exception_frames)
            respond += '\n\n' + module.get_string('error', error=html.escape(exception_frames))
        else:
            respond += '\n'
            if result.returned is not None and len(str(result.returned)) < 500 or result.was_return:
                respond += '\n' + module.get_string('return', result=html.escape(str(result.returned)))

            respond += '\n' + module.get_string('time_spent', delta=round(executing_time, 7))
            getting_input_time = result.console.getting_input_time
            if getting_input_time > 0:
                executing_time -= getting_input_time
                respond += '\n' + module.get_string('time_spent_without_input', delta=round(executing_time, 7))

    if len(respond) >= 4096:
        text = utils.split_string(respond)

        await message.edit_text(text=text[0] + '</code>', parse_mode=pyrogram.enums.ParseMode.HTML)

        reply_to = message
        for i in range(1, len(text)):
            reply_to = await reply_to.reply_text(text='<code>' + text[i] + '</code>',
                                                 parse_mode=pyrogram.enums.ParseMode.HTML)

    else:
        await message.edit_text(respond, parse_mode=pyrogram.enums.ParseMode.HTML)


def define_right_message(_, __, msg):
    try:
        global _waiting_input_list

        reply_msg = msg.reply_to_message

        chat = getattr(reply_msg.chat, 'id', reply_msg.from_user.id)
        key = (chat, reply_msg.id)
        return key in _waiting_input_list and _waiting_input_list[key] is None
    except Exception:
        pass
    return False


@Client.on_message(filters.text & filters.reply &
                   filters.create(func=define_right_message, __doc__='string_id=define_right_message_docs'))
async def getting_input(_, message):
    reply_msg = message.reply_to_message
    chat = getattr(reply_msg.chat, 'id', reply_msg.from_user.id)
    key = (chat, reply_msg.id)
    _waiting_input_list[key] = message.text


def reformat_exception_frames(exception_frames, code):
    exception_frames = exception_frames.strip('\n').split('\n')
    start_slice = 1
    end_slice = 1
    while end_slice < len(exception_frames):
        if re.search(r'( {2}File \"<string>\", line (\d+).*)', exception_frames[end_slice]):
            del exception_frames[start_slice:end_slice]
            break
        end_slice += 1
    exception_frames = '\n'.join(exception_frames)
    for match in re.finditer(r'( {2}File \"<string>\", line (\d+), in .+\n)', exception_frames):
        line = code.split('\n')[int(match.group(2)) - 2].strip(' ')
        exception_frames = re.sub(match.group(1), f'\g<0>    {line}\n', exception_frames)

    exception_frames = re.sub(r'( {2}File \".+?\\).+?\\.+?(\\.+", line (\d+), in .+\n)', '\g<1>...\g<2>',
                              exception_frames)
    return exception_frames



