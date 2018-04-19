import json
from threading import Event
import wakeonlan
from ws4py.client.threadedclient import WebSocketClient
import yaml

from drivers.param_parser import ParamParser


class WebOS(WebSocketClient):

    def __init__(self, config, logger, use_numeric_key=False):
        super(WebOS, self).__init__("ws://" + config['hostName'] + ':' +
            str(config['port']),  exclude_headers=["Origin"])
        self.config = config
        self.connected = False
        self.connectEvent = Event()
        self.curID = 0
        self.callbacks = {}
        self.clientKey = None
        self.logger = logger
        self.paramParser = ParamParser(config, use_numeric_key)
        try:
            with open(config['clientKeyFile'], 'r') as clientKeyInput:
                self.clientKey = yaml.load(clientKeyInput)
        except:
            pass

        try:
            with open(config['macFile'], 'r') as macInput:
                self.config.update(yaml.load(macInput))
        except:
            pass

        self.sock.settimeout(5)
        try:
            self.connect()
        except:
            logger.debug('Websocket timeout. Possibly device is off')

        logger.info('Loaded %s driver', __name__)

    def start(self):
        pass

    def saveClientKey(self):
        with open(self.config['clientKeyFile'], 'w') as clientKeyOutput:
            yaml.safe_dump(self.clientKey, clientKeyOutput, allow_unicode=True,
                encoding='utf-8')
            clientKeyOutput.close()

    def opened(self):
        self.connected = True
        if self.clientKey:
            self.config['registerCommand'].update(self.clientKey)
        self.sendCommand('register', 'register', None,
            self.config['registerCommand'], False)

    def closed(self, code, reason=None):
        self.connected = False
        self.connectEvent.clear()
        self.logger.warn('LG TV Connection closed %s, %s', code, reason)

    def received_message(self, data):
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

    def is_connected(self):
        return self.connected

    def sendCommand(self, prefix, type, uri, payload=None, shouldWait=True):
        if not self.connected:
            try:
                self.connect()
                self.connectEvent.wait(self.config['timeout']
                    if self.clientKey else self.config['promptTimeout'])
            except:
                raise Exception('Driver ' + __name__ +
                    ' cannot connect to device')

        id = prefix + str(self.curID)
        message = {
            'type': type,
            'id': id
        }

        if payload:
            message['payload'] = payload

        if uri:
            message['uri'] = 'ssap://' + uri

        self.send(json.dumps(message))
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

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName, command in self.config['commands'].items():
                commandList.append({
                    'name': commandName,
                    'method': 'GET' if command.get('result', False) else 'PUT'
                })
            return {
                'driver': __name__,
                'commands': commandList
                }

        command = self.config['commands'][commandName]
        if not command.get('result'):
            raise Exception('Invalid command for ' + __name__ +
                ' and method: ' + commandName)

        result = {
            'driver': __name__,
            'command': commandName,
            'output': self.sendCommand('', 'request', command['uri'])
        }

        self.process_result(commandName, command, result)

        return result

    def executeCommand(self, commandName, args=None):
        if commandName == 'toggle_mute':
            output = self.getData('status')

            if 'error' in output['output']:
                return output

            return self.executeCommand('mute',
                'off' if output['output']['payload']['mute'] else 'on')
        elif commandName == 'power_on':
            self.logger.debug('Sending wake up command to %s', self.config['mac'])
            wakeonlan.send_magic_packet(self.config['mac'])
            return {
                'driver': __name__,
                'command': commandName,
                'output': ''
            }

        command = self.config['commands'][commandName]
        if command.get('result'):
            raise Exception('Invalid command for ' + __name__ +
                ' and method: ' + commandName)

        argKey = command.get('argKey')
        argData = None
        if args:
            if not argKey:
                raise Exception('Command in ' + __name__ +
                    ': ' + commandName + ' isn''t configured for arguments')

            args = self.paramParser.translate_param(command, args)

            argData = { argKey: args }
            if command.get('acceptsBool'):
                argData[argKey] = args == 'true' or args == 'on'
            elif command.get('acceptsNumber'):
                try:
                    argData[argKey] = int(args)
                except ValueError:
                    pass
        elif argKey:
            raise Exception('Command in ' + __name__ +
                ': ' + commandName + ' expects for arguments')

        result = {
            'driver': __name__,
            'command': commandName,
            'output': self.sendCommand('', 'request', command['uri'], argData),
            'args': argData
        }

        return result

    def process_result(self, commandName, command, result):
        if 'argKey' in command:
            param = result['output']['payload'][command['argKey']]
            result['result'] = self.paramParser.translate_param(command, param)
