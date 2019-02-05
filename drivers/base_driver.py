from drivers.param_parser import ParamParser


class BaseDriver(object):

    def __init__(self, config, logger, use_numeric_key=False):
        self.config = config
        self.use_numeric_key = use_numeric_key
        self.connected = False
        self.logger = logger
        self.configure()

    def configure(self, data=None):
        if data is not None:
            self.config.update(data)

        self.paramParser = ParamParser(self.config, self.use_numeric_key)
        self.connectionDescription = (self.config.get('hostName', '') + ':' +
            str(self.config.get('port', 0)))

    def start(self):
        try:
            if not self.connected:
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

    def getCommand(self, commandName):
        return self.config['commands'].get(commandName)

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

        if args is not None:
            args = self.paramParser.translate_param(command, str(args))

            if command.get('acceptsBool') and type(args) is not bool:
                args = args == 'true' or args == 'on'
            elif command.get('acceptsNumber'):
                args = str(int(args))
            elif command.get('acceptsPct'):
                args = float(args)/100
            elif command.get('acceptsFloat'):
                args = '{0:g}'.format(float(args))
            elif command.get('acceptsHex'):
                args = hex(int(args))[2:].upper()

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

        if args is not None:
            result['args'] = args

        return result

    def process_result(self, commandName, command, result):
        output = None
        try:
            if command.get('acceptsNumber'):
                output = int(result['output'])
            elif command.get('acceptsFloat'):
                output = float(result['output'])
            elif command.get('acceptsPct'):
                output = int(float(result['output']) * 100)
            elif command.get('acceptsHex'):
                output = int(result['output'], 16)
            else:
                output = self.paramParser.translate_param(command, result['output'],
                    None, False)
        except:
            pass

        if output is not None:
            result['result'] = output

    @staticmethod
    def processParams(config, param):
        return False

    @staticmethod
    def discoverDevices(config):
        return None
