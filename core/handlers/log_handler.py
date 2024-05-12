import json
import os
from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('log'))
async def log_handler(app, message):
    file_path = app.get_config_parameter('logs_directory')
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_path = os.path.join(file_path, 'modules')
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    directories = os.listdir(file_path)

    counters = {}
    for i in directories:
        if os.path.isdir(os.path.join(file_path, i)):
            counters[i] = 0
            for j in os.listdir(os.path.join(file_path, i)):
                filename = os.path.join(os.path.join(file_path, i), j)
                if not filename.endswith('.json'):
                    continue
                file = json.loads(open(filename, 'r', encoding='utf8').read())
                if not isinstance(file, list):
                    continue
                counters[i] += len(file)
        else:
            filename = os.path.join(os.path.join(file_path, i), j)
            if not filename.endswith('.json'):
                continue
            file = json.loads(open(filename, 'r', encoding='utf8').read())
            if not isinstance(file, list):
                continue
            counters[i] = len(file)


    print(counters)
