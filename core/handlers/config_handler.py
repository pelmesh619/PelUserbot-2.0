from pyrogram import Client, filters


@Client.on_message(filters.me & filters.command('config'))
async def config_handler(app, message):
    module_name = ' '.join(message.command[1:])
    if not module_name:
        await message.reply_text(app.get_string('config_enter_module_name', _module_id='core.handlers'))
        return

    try:
        module = app.get_module(module_name)
    except KeyError as e:
        await message.reply_text(
            app.get_string('config_module_not_found', module_name=module_name, _module_id='core.handlers')
        )
        return

    if len(module.config) == 0:
        return await message.reply_text(
            app.get_string(
                'config_module_does_not_have_config',
                module_name=module.full_name(),
                _module_id='core.handlers'
            )
        )

    parameters = ''

    for i, param in enumerate(module.config):
        parameters += app.get_string(
            'config_parameter_template',
            num=i+1,
            name=param,
            value=module.config[param],
            default_value=app.get_string(
                'config_default_template',
                value=module.default_config.get(param),
                _module_id='core.handlers'
            ) if module.default_config.get(param, None) else '',
            _module_id='core.handlers'
        )

    await message.reply(
        app.get_string(
            'config_config_template',
            parameters=parameters,
            module_name=module.full_name(),
            _module_id='core.handlers'
        )
    )
