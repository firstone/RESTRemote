import socket
import time

from drivers.param_parser import ParamParser


class TivoIP(object):

    def __init__(self, config, logger, use_numeric_key=False):
        self.config = config
        self.logger = logger
        self.paramParser = ParamParser(config, use_numeric_key)

        logger.info('Loaded %s driver', __name__)

    def start(self):
        pass

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName in self.config['commands'].keys():
                commandList.append({
                    'name': commandName,
                    'method': 'PUT'
                })

            return {
                'driver': __name__,
                'commands': commandList
                }

        raise Exception('Invalid command for ' + __name__ + ': ' + commandName)

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

    def sendCommand(self, command, args=None):
        result = ''
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((self.config['hostName'], self.config['port']))
            conn.settimeout(self.config['timeout'])
            conn.send(command['code'].encode())
            if command.get('argument') and args:
                conn.send(self.paramParser.translate_param(command, args).encode())
            conn.send('\r\n'.encode())
            if command.get('response', False):
                result = conn.recv(1024).decode()
            delay = command.get('delay')
            if delay:
                time.sleep(delay)
        except socket.timeout:
            pass
        conn.close()
        return result

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
