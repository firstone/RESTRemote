from drivers.param_parser import ParamParser


class BaseDriver(object):

    def __init__(self, config, logger, use_numeric_key=False):
        self.config = config
        self.paramParser = ParamParser(config, use_numeric_key)
        self.connected = False
        self.logger = logger
        self.connectionDescription = config.get('hostName', '') + ':' + str(config.get('port', 0))

    def start(self):
        try:
            self.connect()
        except:
            self.logger.exception('Connection to %s failed',
                self.connectionDescription)

    def connect(self):
        pass

    def is_connected(self):
        try:
            if not self.connected:
                self.connect()
        except:
            pass

        return self.connected

    def hasCommand(self, commandName):
        return commandName in self.config['commands']

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName, command in self.config['commands'].items():
                commandList.append({
                    'name': commandName,
                    'method': 'GET' if command.get('result', False) else 'PUT'
                })
            return {
                'driver': self.__class__.__name__,
                'commands': commandList
            }

        command = self.config['commands'][commandName]
        if not command.get('result'):
            raise Exception('Invalid command for ' + __name__ +
                ' and method: ' + commandName)

        result = {
            'driver': self.__class__.__name__,
            'command': commandName,
        }

        try:
            result['output'] = self.sendCommandRaw(commandName, command)
            self.process_result(commandName, command, result)
        except:
            self.connected = False
            raise
        return result

    def sendCommandRaw(self, commandName, command, args=None):
        pass

    def executeCommand(self, commandName, args=None):
        command = self.config['commands'][commandName]

        if args:
            if command.get('acceptsBool') and type(args) is not bool:
                args = args == 'true' or args == 'on'
            elif command.get('acceptsNumber'):
                args = str(int(args))
            elif command.get('acceptsFloat'):
                args = '{0:g}'.format(float(args))
            elif command.get('acceptsHex'):
                args = hex(int(args))[2:]
            else:
                args = self.paramParser.translate_param(command, args)

        result = {
            'driver': __name__,
            'command': commandName,
        }

        try:
            result['output'] = self.sendCommandRaw(commandName, command, args)
            self.process_result(commandName, command, result)
        except:
            self.connected = False
            raise

        if args:
            result['args'] = args

        return result

    def process_result(self, commandName, command, result):
        if command.get('acceptsNumber'):
            output = int(result['output'])
        elif command.get('acceptsFloat'):
            output = float(result['output'])
        elif command.get('acceptsHex'):
            output = int(result['output'], 16)
        else:
            output = self.paramParser.translate_param(command, result['output'],
                None, False)

        if output:
            result['result'] = output
