import socket
import time

from drivers.param_parser import ParamParser


class DenonAVR(object):

    BUF_SIZE = 4096
    RESPONSE_DELAY = 1

    def __init__(self, config, logger, use_numeric_key=False):
        self.config = config
        self.paramParser = ParamParser(config, use_numeric_key)
        self.connected = False
        self.logger = logger
        logger.info('Loaded %s driver', __name__)

    def start(self):
        try:
            self.connect()
        except:
            self.logger.exception('Connection to ' + self.config['hostName'] +
                ':' + str(self.config['port']) + ' failed')

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.config['hostName'], self.config['port']))
        self.conn.settimeout(self.config['timeout'])
        self.connected = True

    def is_connected(self):
        return self.connected

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

    def sendCommand(self, command):
        if not self.connected:
            self.connect()

        result = ''
        try:
            self.conn.send(command.encode())
            self.conn.send('\n'.encode())
            time.sleep(self.RESPONSE_DELAY)
            result = self.conn.recv(self.BUF_SIZE).decode()
        except socket.timeout:
            pass
        return result[:-1].split('\r') if result else result

    def executeCommand(self, commandName, args=None):
        command = self.config['commands'][commandName]
        commandStr = command['code']

        if args:
            commandStr += self.paramParser.translate_param(command, args).upper()

        result = {
            'driver': __name__,
            'command': commandName,
            'output': self.sendCommand(commandStr)
        }

        if args:
            result['args'] = args

        self.process_result(commandName, command, result)

        return result

    def process_result(self, commandName, command, result):
        if len(result) == 0:
            return

        if commandName == 'current_volume':
            output = self.get_last_output(result['output'], 'MV', 'MVMAX')
            if len(output) > 2:
                output = output[:2] + '.5'
            else:
                output = output + '.0'
            output = float(output)
        else:
            output = self.paramParser.translate_param(command,
                self.get_last_output(result['output'], command['code'][:2]))

        if output:
            result['result'] = output

    def get_last_output(self, output, prefix, except_prefix=None):
        last = None

        for line in output:
            if line.startswith(prefix) and (not except_prefix or not line.startswith(except_prefix)):
                last = line[len(prefix):]

        return last
