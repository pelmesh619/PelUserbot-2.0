import re
import traceback

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


def format_traceback(exc, app, script_string='', last_frame=None):
    traceback_frames = []
    traceback_info = traceback.TracebackException(*exc)
    for frame in traceback_info.stack:
        new_filename = re.sub(r'(.+?[/\\]).+([/\\].+?[/\\].+?)', '\g<1>...\g<2>', frame.filename)
        code_line = frame.line
        if script_string and new_filename == '<string>':
            code_line = script_string.split('\n')[frame.lineno - 1].strip(' ')
        traceback_frames.append(
            app.get_core_string(
                'traceback_frame',
                line=frame.lineno,
                filename=new_filename,
                name=frame.name,
                code=code_line
            )
        )

    error_args = exc[1].args
    if last_frame:
        new_filename = re.sub(r'(.+?[/\\]).+([/\\].+?[/\\].+?)', '\g<1>...\g<2>', last_frame[0])
        traceback_frames.append(
            app.get_core_string(
                'traceback_frame_without_name',
                line=last_frame[1],
                filename=new_filename,
                code=last_frame[3]
            ) + ' ' * (last_frame[2] - 1) + '^'
        )
        error_args = error_args[:1]

    return app.get_core_string(
        'traceback_template',
        traceback='\n'.join(traceback_frames),
        error=exc[0].__name__,
        error_text='; '.join([repr(i) for i in error_args])
        if error_args else app.get_core_string('traceback_no_detail')
    )
