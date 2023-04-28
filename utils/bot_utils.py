import html
import inspect
import time
import asyncio
from typing import Union

import pyrogram
from pyrogram import Client

from utils.memory_utils import memory_to_string


async def call_filters(filters, client, message):
    if inspect.iscoroutinefunction(filters.__call__):
        return await filters(client, message)
    else:
        return await client.loop.run_in_executor(
            client.executor,
            filters,
            client, message
        )


class Answer:
    def __init__(self, filters, possible_results, amount_answers=1,
                 is_multiple=False, deleting_message_timeout: float = -1
                 ):
        self.result = None
        self.results = []
        self.is_multiple = is_multiple
        self.filters = filters
        self.possible_results = possible_results
        self.amount_answers = amount_answers
        self.queue = []
        self.answers = []
        self.deleting_message_timeout = deleting_message_timeout




async def _wait_answer(app, remaining_time, start, key):
    while time.time() < remaining_time + start and app.answers[key].result is None:
        await asyncio.sleep(0.5)



async def wait_answer(
        message: pyrogram.types.Message,
        filters: callable = lambda *_: True,
        possible_results: Union[list, tuple] = (),
        timeout: float = float('inf'),
        deleting_message_timeout: float = -1
):
    app = message._client
    if not hasattr(app, 'answers'):
        app.answers = {}
    key = (getattr(message.chat, 'id', None), message.id)
    app.answers[key] = Answer(filters, possible_results, deleting_message_timeout=deleting_message_timeout)

    start = time.time()

    _ = await _wait_answer(app, timeout, start, key)

    return app.answers.pop(key).result


async def _wait_multiple_answers(app, remaining_time, start, key, amount_answers):
    while time.time() < remaining_time + start and len(app.answers[key].answers) < amount_answers:
        await asyncio.sleep(0.1)
        if app.answers[key].queue:
            answer = app.answers[key].queue.pop()

            yield answer


async def wait_multiple_answers(
        message: pyrogram.types.Message,
        amount_answers: int = 1,
        filters: callable = lambda *_: True,
        possible_results: Union[list, tuple] = (),
        remaining_time: float = float('inf')
):
    key = (getattr(message.chat, 'id', None), message.id)
    app = message._client
    if not hasattr(app, 'answers'):
        app.answers = {}
    app.answers[key] = Answer(filters, possible_results, amount_answers, is_multiple=True)

    start = time.time()

    async for answer in _wait_multiple_answers(app, remaining_time, start, key, amount_answers):
        yield answer

    while app.answers[key].queue:
        yield app.answers[key].queue.pop()

    del app.answers[key]





def get_progress_func(
        message,
        progress_type='percent',
        dot_type='.',
        dot_max_amount=3,
        bar_length=20,
        bar_type=0,
        bar_place_value=None,
        bar_brackets=('[', ']')
):
    counter = 1

    async def progress_func(cur, total, *args):
        nonlocal counter
        counter = counter % dot_max_amount + 1

        if progress_type == 'percent':
            return await message.edit(message.text.html.format(str(round(cur / total * 100, 2)) + '%'))
        elif progress_type == 'dots':
            return await message.edit(message.text.html.format(dot_type * counter))
        elif progress_type == 'memory':
            total_memory = message.get_string.memory_to_string(total, round_value=3)
            cur_memory = message.get_string.memory_to_string(cur, measure=total_memory.measure, round_value=3).value
            return await message.edit(message.text.html.format(str(cur_memory) + '/' + total_memory))
        elif progress_type == 'bar':
            percent = round(cur / total * 100, 2)
            return await message.edit(
                message.text.html.format(
                    html.escape(create_loading_bar(percent, bar_length, bar_type, bar_place_value, bar_brackets))))

    return progress_func


def create_loading_bar(percent, length=10, bar_type=0, place_value=None, brackets=('[', ']')):
    loading_bars = [
        '.=',
        '-|',
        '▒█',
        '░▒▓█',
        ' ▏▎▍▌▋▊▉',
        ' ▁▂▃▄▅▆▇█',
    ]
    percent_string = str(percent) + '%'

    if isinstance(bar_type, int):
        load = loading_bars[bar_type]
    else:
        load = bar_type

    count = len(load) * length * percent // 100

    string = load[-1] * int(count // len(load))
    if len(string) < length:
        string += load[int(count % len(load))]

    if place_value == 'follow':
        if length - len(string) - len(percent_string) < 0:
            string = string[:length - len(percent_string)] + percent_string
        else:
            string += percent_string

    string += load[0] * (length - len(string))

    if place_value == 'left':
        string = percent_string + string[len(percent_string):]

    if place_value == 'right':
        string = string[:length - len(percent_string)] + percent_string

    if place_value == 'middle':
        string = string[:(length - len(percent_string)) // 2] + \
                 percent_string + string[(length + len(percent_string)) // 2:]

    if isinstance(brackets, (tuple, list)) and len(brackets) == 2:
        string = brackets[0] + string + brackets[1]

    return string
