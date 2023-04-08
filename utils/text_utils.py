import re

import pyrogram.enums


def format_text(str_, *args, **kwargs):
    for i, el in enumerate(args, start=1):
        try:
            str_ = str_.replace('{' + str(i) + '}', str(el))
        except Exception as e:
            print(repr(e))
    for i, el in kwargs.items():
        try:
            str_ = str_.replace('{' + str(i) + '}', str(el))
        except Exception as e:
            print(repr(e))

    return str_


def cut_text(text, length=70):
    if len(text) <= length:
        return text

    text = text[:50]
    text = ' '.join(text.split(' ')[:-1]) + '...'

    return text


def split_string(text, chars_per_string=4000):
    texts = []

    while len(text) > 0:
        if len(text) <= chars_per_string:
            texts.append(text)
            text = ''

        if re.search('\n', text[chars_per_string // 3:chars_per_string]):
            for i in range(min(chars_per_string, len(text)) - 1, -1, -1):
                if text[i] == '\n':
                    texts.append(text[:i].strip('\n'))
                    text = text[i + 1:]
                    break
        elif re.search(' ', text[:chars_per_string]):
            for i in range(min(chars_per_string, len(text)) - 1, -1, -1):
                if text[i] == ' ':
                    texts.append(text[:i].strip(' '))
                    text = text[i + 1:]
                    break
        else:
            texts.append(text[:chars_per_string])
            text = text[chars_per_string:]

    counter = 0
    while counter < len(texts):
        if not texts[counter]:
            del texts[counter]
        else:
            counter += 1

    return texts


def get_message_entity(message, type, n=1):
    if not message.entities:
        return
    if isinstance(type, str):
        type = getattr(pyrogram.enums.MessageEntityType, type.upper(), type)

    for entity in message.entities:
        if entity.type == type and n == 1:
            return message.text[entity.offset:entity.offset + entity.length]
        elif entity.type == type:
            n -= 1


def remove_html_tags(string):
    string = re.sub(r'<\/?\w+?.*?>', '', string)

    return string
