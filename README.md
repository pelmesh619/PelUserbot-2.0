# PelUserbot-2.0
PelUserbot, a powerful userbot for Telegram, containing a lot of features.

__Some of PelUserbot's features__:

* __Modules__: PelUserbot can in runtime turn off and on its handlers and modules, so it can expand its functional

* __Scheduler__: PelUserbot has built-in asynchronous scheduler

* __Databases__: PelUserbot offers built-in databases for modules and PelUserbot itself

* __Finite State Machine__: PelUserbot has its own finite state machine for every module

Know more about it in [project's wiki](https://github.com/pelmesh619/PelUserbot-2.0/wiki)!

## Installation

The install is pretty simple, just run in your terminal:

```bash
git clone https://github.com/pelmesh619/PelUserbot-2.0.git
cd PelUserbot-2.0
pip install -r ./requirements.txt
```

Then go to the https://my.telegram.org, create a new app and get your API id and hash. Paste them in config.json file like this:

```json
    "api_id": 1111111,
    "api_hash": "0123456789abcdef0123456789abcdef",
```


To start the PelUserbot, just run

```bash
python main.py
```

After that you will be asked for phone number and access code.

