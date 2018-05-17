import json
import requests

from drivers.base_driver import BaseDriver


class ESP8266(BaseDriver):

    URL = 'http://{}:{}/{}'

    def __init__(self, config, logger, use_numeric_key=False):
        super(ESP8266, self).__init__(config, logger, use_numeric_key)

        logger.info('Loaded %s driver', __name__)

    def connect(self):
        response = requests.get(ESP8266.URL.format(self.config['hostName'],
            self.config['port'], 'ping'))

        if response.ok:
            self.connected = json.loads(response.content)['result'] == 'success'

    def sendCommandRaw(self, commandName, command, args=None):
        commandStr = command.get('code', commandName)
        if args:
            commandStr += args

        response = requests.post(ESP8266.URL.format(self.config['hostName'],
            self.config['port'],
            'sendCode/' + self.config['ir_emitter'] + '/' + commandStr))

        return json.loads(response.content)
