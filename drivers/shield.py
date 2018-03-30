import subprocess


class Shield(object):

    def __init__(self, config):
        self.config = config
        self.executable = config['executable']
        print subprocess.check_output([self.executable, 'connect',
            config['hostName'] + ':' + str(config['port'])])
        print 'Loaded ', __name__, 'driver'

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName in self.config['keycodes'].iterkeys():
                commandList.append({
                    'name': commandName,
                    'method': 'PUT'
                })
            return {
                'driver': __name__,
                'commands': commandList
                }

        raise Exception('Invalid command for ' + __name__ + ': ' + commandName)

    def executeCommand(self, commandName, args=None):
        output = subprocess.check_output([self.executable, 'shell', 'input',
            'keyevent', str(self.config['keycodes'][commandName])])

        result = {
            'driver': __name__,
            'command': commandName,
            'output': output
        }

        if args:
            result['args'] = args

        return result
