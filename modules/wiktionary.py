import re

import requests
import bs4
from pyrogram import Client, filters

from core import Module

module = Module(
    strings={
        'ru': {
            'there_is_no_article': 'Статьи по слову "<a href="{url}">{word}</a>" не существует',
            'definitions': '{word} - это:\n{definitions}',
            'definitions_were_not_found': 'Значение слова "<a href="{url}">{word}</a>" не были найдены:\n\n{text}'
        }
    }
)

ENDPOINT = 'https://ru.wiktionary.org/wiki/'


@Client.on_message(filters.me & filters.command('wiktionary'))
async def wiktionary_handler(app, message):
    word = ' '.join(message.command[1:]).lower()
    url = ENDPOINT + word
    try:
        content = requests.get(url).content
    except Exception as e:
        await message.reply()
        return
    soup = bs4.BeautifulSoup(content, 'html.parser')

    if soup.find_all('div', 'noarticletext'):
        print('no article text')
        await message.reply(message.get_string('there_is_no_article', word=word, url=url),
                            disable_web_page_preview=True)
        return

    definitions = []

    list_ = soup.find_all('ol')
    if not list_:
        text = str(soup.find('div', 'mw-parser-output').tbody.find_all('td')[1]).replace('<br/>', '\n')
        text = text.replace('href="/wiki/', f'href="{ENDPOINT}')
        await message.reply(
            message.get_string('definitions_were_not_found', word=word, text=text, url=url),
            disable_web_page_preview=True,
        )
        return
    else:
        list_ = list_[0]
    for list_item in list_.find_all('li'):
        list_item = str(list_item).replace('<li>', '').replace('</li>', '')
        list_item = re.sub(r'<span class="example-select".*?>(.+?)</span>', '<u>\g<1></u>', list_item)
        list_item = re.sub(r'</?span.*?>', '', list_item)
        list_item = re.sub(r'</?i>', '', list_item)
        list_item = re.sub(r'\[\d+\] *', '', list_item)
        list_item = list_item.replace('href="/wiki/', f'href="{ENDPOINT}')
        elements = list_item.split('◆')
        definition = elements[0]
        if len(elements) > 1:
            definition += '◆ <i>' + elements[1].strip() + '</i>'

        definitions.append('    ' + definition)

    await message.reply(
        message.get_string('definitions', word=word.capitalize(), definitions='\n'.join(definitions)),
        disable_web_page_preview=True,
    )
