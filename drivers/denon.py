import socket
import time


class Denon(object):

    BUF_SIZE = 4096
    RESPONSE_DELAY = 1

    def __init__(self, config):
        self.config = config
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.config['hostName'], self.config['port']))
        self.conn.settimeout(self.config['timeout'])
        print 'Loaded', __name__, 'driver'

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName, command in self.config['commands'].iteritems():
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

        return {
            'driver': __name__,
            'command': commandName,
            'output': self.sendCommand(command['code'])
        }

    def sendCommand(self, command):
        result = ''
        try:
            self.conn.send(command)
            self.conn.send('\n')
            time.sleep(self.RESPONSE_DELAY)
            result = self.conn.recv(self.BUF_SIZE)
        except socket.timeout:
            pass
        return result[:-1].split('\r') if result else result

    def executeCommand(self, commandName, args=None):
        command = self.config['commands'][commandName]['code']

        if args:
            if 'values' in command:
                args = command['values'][args]

            command += args.upper()

        result = {
            'driver': __name__,
            'command': commandName,
            'output': self.sendCommand(command)
        }

        if args:
            result['args'] = args

        return result
