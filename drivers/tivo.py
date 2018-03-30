import socket
import time


class Tivo(object):

    def __init__(self, config):
        self.config = config
        print 'Loaded', __name__, 'driver'

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName in self.config['commands'].iterkeys():
                commandList.append({
                    'name': commandName,
                    'method': 'PUT'
                })

            return {
                'driver': __name__,
                'commands': commandList
                }

        raise Exception('Invalid command for ' + __name__ + ': ' + commandName)

    def sendCommand(self, command):
        result = ''
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.config['hostName'], self.config['port']))
        conn.settimeout(self.config['timeout'])
        try:
            conn.send(command['code'])
            conn.send('\r\n')
            if command.get('response', False):
                result = conn.recv(1024)
            delay = command.get('delay')
            if delay:
                time.sleep(delay)
        except socket.timeout:
            pass
        conn.close()
        return result

    def executeCommand(self, commandName, args=None):
        output = []
        command = self.config['commands'][commandName]
        if 'commands' in command:
            for item in command['commands']:
                output.append(self.sendCommand(item))
        else:
            output.append(self.sendCommand(command))

        result = {
            'driver': __name__,
            'command': commandName,
            'output': output
        }

        if args:
            result['args'] = args

        return result
