import io
import re
import time
import sys
import html
import logging
import traceback

from pyrogram import Client, filters
from core import Module, Author, bot_filters

import utils
from utils import bot_utils, format_traceback

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
            'code_and_output_regex': 'Код:\n(.*)\nВывод:\n.*',
            'code_and_return_regex': 'Код:\n(.*)\nВозвращено: .*',
            'code_and_error_regex': 'Код:\n(.*)\nВозникла ошибка:\n.*',
            'code_and_interpretation_error_regex': 'Код:\n(.*)\nВозникла ошибка интерпретации:\n.*',
            'code_and_time_spent_regex': 'Код:\n(.*)\nПотрачено времени: .* с',
        },
        'en': {
            'pyexec_module_name': 'Executor Pyexec',
            'description': 'Executes Python code. Supports input function and error\'s traceback.',

            'code_edited_filter': 'with edited code inside old message',
            # 'define_right_message_docs': 'являющиеся ответом на сообщение, ждущее ввод',
            'code': '<b>Code</b>:\n<pre>{code}</pre>',
            'output': '<b>Output</b>:\n<code>{output}</code>',
            'no_args': '<b>Enter in command code or reply command to message to execute Python code</b>',
            'return': '<b>Returned</b>: <code>{result}</code>',
            'error': '<b>Error raised</b>:\n<code>{error}</code>',
            'interpretation_error': '<b>Interpretation error raised</b>:\n<code>{error}</code>',
            'time_spent': '<b>Time spent</b>: {delta} sec',
            'time_spent_without_input': '<b>Time spent without getting input</b>: {delta} sec',
            'waiting_input': 'Waiting user\'s input...',
            'program_needs_input': 'Program needs input (reply to this message)\n\n<code>{prompt}</code>',
            'code_and_output_regex': 'Код:\n(.*)\nВывод:\n.*',
            'code_and_return_regex': 'Код:\n(.*)\nВозвращено: .*',
            'code_and_error_regex': 'Код:\n(.*)\nВозникла ошибка:\n.*',
            'code_and_interpretation_error_regex': 'Код:\n(.*)\nВозникла ошибка интерпретации:\n.*',
            'code_and_time_spent_regex': 'Код:\n(.*)\nПотрачено времени: .* с',
        },
        'ge': {
            'code': '<b>Code</b>:\n<pre>{code}</pre>',
            'output': '<b>Ausgabe</b>:\n<code>{output}</code>',

        }

    },
)


class Console:
    def __init__(self, message=None, respond=''):
        self.file = ''
        self.message = message
        self.respond = respond
        self.getting_input_time = 0

    @staticmethod
    def write(str_, *_, **__):
        print(str_, end='', file=sys.__stdout__)

    def print(self, *args, sep=' ', end='\n'):
        print(*args, sep=sep, end=end, file=sys.__stdout__)
        self.file += sep.join([str(i) for i in args]) + end

    # noinspection PyProtectedMember
    async def input(self, prompt='', *_, **__):
        self.print(prompt, end='')

        current_time = time.time()
        try:
            new_respond = self.respond
            if self.file:
                new_respond += '\n\n' + module.get_string('output', output=html.escape(self.file))
            await self.message.edit(new_respond + '\n\n' + module.get_string('waiting_input'))
        except Exception as e:
            print(e)
            # TODO logs

        input_respond = module.get_string('program_needs_input', prompt=prompt)
        input_message = await self.message.reply(input_respond)
        answer = await bot_utils.wait_answer(input_message, filters.text, timeout=30)

        if answer is None:
            await input_message.edit(
                input_respond + '\n\n' +
                self.message._client.get_core_string('message_is_outdated')
            )
            raise TimeoutError(self.message._client.get_core_string('message_is_outdated'))
        else:
            input_value = answer.text

        new_respond = self.respond
        if not self.file:
            new_respond += '\n\n' + module.get_string('output', output=html.escape(self.file + input_value))
        self.print(input_value)
        try:
            await self.message.edit(new_respond + '\n\n' + module.get_string('waiting_input'))
        except Exception as e:
            print(e)

        await input_message.edit(input_respond + f'<code>{input_value}</code>')

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
            interpretation_error=None,
            modified_script=None
    ):
        self.console = console
        self.returned = returned
        self.executing_time = executing_time
        self.was_return = was_return
        self.error = error
        self.error_console = error_console
        self.interpretation_error = interpretation_error
        self.modified_script = modified_script


def add_to_global(func):
    globals()[func.__name__] = func
    return func


# noinspection PyBroadException
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
            code = return_code
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
    result = Result(console, returned, bool(return_match), executing_time, error, error_console, modified_script=code)

    return result


def kwargs_to_str(dict_, **kwargs):
    args = []
    for i in kwargs:
        dict_[i] = kwargs[i]
    for i in dict_:
        args.append(f'{i}={i}')

    return ', '.join(args)


def edit_code_filter(_, __, message):
    possible_results = ['output', 'return', 'error', 'interpretation_error', 'time_spent']
    possible_results = ['code_and_' + i + '_regex' for i in possible_results]
    regexes = [message.get_string(i) for i in possible_results]

    for r in regexes:
        match = re.search(r, message.text, re.S)

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


@Client.on_edited_message(filters.me & bot_filters.i_am_user & code_edited_filter)
@Client.on_message(filters.me & filters.command('exec'))
async def execute_handler(peluserbot, message):
    script = getattr(message, 'script', None) or ' '.join(message.text.split(' ')[1:])
    is_edited = hasattr(message, 'script')
    exec_msg = message

    if not script:
        if not message.reply_to_message:
            await message.reply(module.get_string('no_args'))
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

    if not is_edited:
        bot_message = await message.reply(respond)
    else:
        bot_message = await message.edit(respond)

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
        '_message': message,
    }

    result = await asyncexec(script, **kwargs)
    executing_time = result.executing_time
    output = result.console.file.strip('\n')
    if result.interpretation_error:
        exception_frames = format_traceback(
            result.interpretation_error,
            peluserbot,
            result.modified_script,
            result.interpretation_error[1].args[1]
        )
        respond += '\n\n' + module.get_string('interpretation_error', error=html.escape(exception_frames))
    else:

        if output:
            respond += '\n\n' + module.get_string('output', output=html.escape(output))
        if result.error:
            exception_frames = format_traceback(result.error, peluserbot, result.modified_script)
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

        await bot_message.edit_text(text=text[0] + '</code>')

        reply_to = bot_message
        for i in range(1, len(text)):
            reply_to = await reply_to.reply_text(text='<code>' + text[i] + '</code>')

    else:
        await bot_message.edit_text(respond)
