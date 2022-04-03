import json
from threading import Event
import wakeonlan
from ws4py.client.threadedclient import WebSocketClient
import yaml

from drivers.base_driver import BaseDriver


class WebOS(BaseDriver):

    def __init__(self, config, logger, use_numeric_key=False):
        super(WebOS, self).__init__(config, logger, use_numeric_key)
        self.connectEvent = Event()
        self.curID = 0
        self.callbacks = {}
        self.clientKey = None
        self.client = None
        try:
            with open(config['clientKeyFile'], 'r') as clientKeyInput:
                self.clientKey = yaml.safe_load(clientKeyInput)
        except:
            pass

        logger.info('Loaded %s driver', self.__class__.__name__)

    def saveClientKey(self):
        with open(self.config['clientKeyFile'], 'w') as clientKeyOutput:
            yaml.safe_dump(self.clientKey, clientKeyOutput, allow_unicode=True,
                           encoding='utf-8')
            clientKeyOutput.close()

    def on_open(self):
        self.connected = True
        if self.clientKey:
            self.config['registerCommand'].update(self.clientKey)
        self.sendCommandRaw('register', self.config['registerCommand'], None,
                            False)

    def on_close(self, code, reason=None):
        self.connected = False
        self.connectEvent.clear()
        self.logger.warn('LG TV Connection closed %s, %s', code, reason)

    def on_message(self, data):
        self.logger.debug('Received %s', data)
        message = json.loads(str(data))
        if message['id'] == 'register0':
            if message['type'] == 'error':
                self.logger.error('Connection issue %s', message['error'])
            elif message['type'] == 'registered':
                if not self.clientKey:
                    self.clientKey = message['payload']
                    self.saveClientKey()
                self.connectEvent.set()
        callback = self.callbacks.get(message['id'])
        if callback:
            callback['data'] = message
            callback['event'].set()

    def connect(self):
        try:
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
            self.client = WebSocketClient("ws://" + self.config['hostName'] + ':' +
                                          str(self.config['port']),  exclude_headers=["Origin"])
            self.client.opened = self.on_open
            self.client.closed = self.on_close
            self.client.received_message = self.on_message
            self.client.sock.settimeout(self.config['timeout'])
            self.client.connect()
            self.connectEvent.wait(self.config['timeout']
                                   if self.clientKey else self.config['promptTimeout'])
        except:
            pass

    def sendCommandRaw(self, commandName, command, args=None, shouldWait=True):
        if commandName == 'power_on':
            mac = self.config.get('mac')
            if mac is None:
                self.logger.error(
                    'Error sending power on command. MAC is not set up')
            else:
                ip = self.config.get('broadcastAddress')
                if ip == '':
                    ip = '255.255.255.255'

                self.logger.debug('Sending wake up command to %s (%s)', mac, ip)

                wakeonlan.send_magic_packet(mac, ip_address=ip)
            return ''
        elif commandName == 'toggle_mute':
            output = self.sendCommandRaw(
                'status', self.config['commands']['status'])

            if 'error' in output:
                return output

            return self.sendCommandRaw('mute', self.config['commands']['mute'],
                                       False if output['payload']['mute'] else True)

        if not self.connected:
            try:
                self.connect()
            except:
                raise Exception('Driver ' + __name__ +
                                ' cannot connect to device')

        message = {}
        id = str(self.curID)

        if commandName == 'register':
            message['type'] = 'register'
            message['payload'] = command
            id = 'register' + id
        else:
            message['type'] = 'request'

        message['id'] = id

        argKey = command.get('argKey')
        argData = None
        if args is not None:
            if not argKey:
                raise Exception('Command in ' + __name__ +
                                ': ' + commandName + ' isn''t configured for arguments')

            argData = {argKey: args}

        if argData:
            message['payload'] = argData

        if 'uri' in command:
            message['uri'] = 'ssap://' + command['uri']

        self.logger.debug('Sending %s', message)
        self.client.send(json.dumps(message))
        self.curID += 1
        event = Event()
        callback = {
            'event': event,
            'data': {}
        }

        self.callbacks[id] = callback

        if shouldWait:
            event.wait(self.config['timeout'])
            return callback['data']

        return ''

    def process_result(self, commandName, command, result):
        if 'argKey' in command:
            payload = result['output'].get('payload')
            if not payload:
                self.logger.warning("Missing payload for command %s: %s",
                                    commandName, result['output'])
                return
            param = payload.get(command['argKey'])
            if param is not None:
                result['result'] = self.paramParser.translate_param(
                    command, param)
