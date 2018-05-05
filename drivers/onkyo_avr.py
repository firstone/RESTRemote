import socket

from drivers.param_parser import ParamParser


class OnkyoAVR(object):

    INIT_DATA = bytearray(
        [73, 83, 67, 80, 0, 0, 0, 16, 0, 0, 0, 8, 1, 0, 0, 0, 33, 49]
    )

    def __init__(self, config, logger, use_numeric_key=False):
        self.config = config
        self.paramParser = ParamParser(config, use_numeric_key)
        self.connected = False
        self.logger = logger
        logger.info('Loaded %s driver', __name__)

    def start(self):
        pass

    def is_connected(self):
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((self.config['hostName'], self.config['port']))
            conn.settimeout(self.config['timeout'])
            conn.close()
            return True
        except:
            pass

        return False

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
            'output': self.sendCommand(command['code'])
        }
        self.process_result(commandName, command, result)
        return result

    def sendCommand(self, command, args=None):
        result = ''
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((self.config['hostName'], self.config['port']))
            conn.settimeout(self.config['timeout'])
            commandStr = command['code']
            if (command.get('argument') or 'value_set' in command) and args:
                commandStr += self.paramParser.translate_param(command, args)
            conn.send(self.convertToTCPBytes(commandStr))
            if command.get('response', False):
                result = conn.recv(1024)
        except socket.timeout:
            pass
        conn.close()
        return result

    def convertToTCPBytes(self, strData):
        strData = strData + '\r'
        tempdata = strData.encode('ascii')
        data = OnkyoAVR.INIT_DATA + tempdata
        data[11] = len(strData) + 2
        return data

    def executeCommand(self, commandName, args=None):
        self.logger.debug('Driver %s executing command %s', __name__, commandName)
        output = []
        command = self.config['commands'][commandName]
        if 'commands' in command:
            for item in command['commands']:
                output.append(self.sendCommand(item, args))
        else:
            output.append(self.sendCommand(command, args))

        result = {
            'driver': __name__,
            'command': commandName,
            'output': output
        }

        if args:
            result['args'] = args

        return result

    def process_result(self, commandName, command, result):
        if len(result) == 0:
            return

        val = result['output'][21:23].decode("utf-8")
        if commandName.find('volume') >= 0:
            output = int(val, 16)
        else:
            output = self.paramParser.translate_param(command, val)

        if output:
            result['result'] = output
