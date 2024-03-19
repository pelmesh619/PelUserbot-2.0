from core import Peluserbot

__version__ = '2.0.0-alpha2'

client = Peluserbot(app_version=__version__, config_filename='config.json')

client.run()
