import subprocess

from drivers.param_parser import ParamParser


class Android(object):

    def __init__(self, config, logger, use_numeric_key=False):
        self.config = config
        self.executable = config['executable']
        self.logger = logger
        self.paramParser = ParamParser(config, use_numeric_key)
        self.connectStr = self.config['hostName'] + ':' + str(self.config['port'])
        self.connected = False
        logger.info('Loaded %s driver', __name__)

    def start(self):
        try:
            self.connect()
        except:
            self.logger.exception('Error connecting to ' + self.connectStr)

    def connect(self):
        self.logger.debug('ADB status %s', subprocess.check_output(
            [self.executable, 'connect', self.connectStr]).decode())
        self.logger.debug('ADB status %s', subprocess.check_output(
            [self.executable, 'connect', self.connectStr]).decode())
        output = subprocess.check_output([self.executable, 'devices']).decode().split('\n')
        for line in output:
            if line.startswith(self.connectStr):
                if line.split('\t')[1] == 'online':
                    self.connected = True

        raise IOError('Connection to ' + self.connectStr +
            ' failed. If device is accessible, try restarting it')

    def is_connected(self):
        return self.connected

    def getData(self, commandName, args=None):
        if commandName == 'commands':
            commandList = []
            for commandName, commandData in self.config['commands'].items():
                commandList.append({
                    'name': commandName,
                    'method': 'GET' if commandData.get('result') else 'PUT'
                })
            return {
                'driver': __name__,
                'commands': commandList
                }
        elif commandName == 'get_app_list':
            return {
                'driver': __name__,
                'command': 'get_app_list',
                'output': self.getCommandList()
            }

        raise Exception('Invalid command for ' + __name__ + ': ' + commandName)

    def executeCommand(self, commandName, args=None):
        if not self.connected:
            self.connect()

        if commandName == 'start_app':
            args = self.paramParser.translate_param(
                self.config['commands'][commandName], args)
            output = subprocess.check_output([self.executable, 'shell', 'am',
                'start', '-n', args])
        else:
            output = subprocess.check_output([self.executable, 'shell', 'input',
                'keyevent', str(self.config['commands'][commandName]['code'])])

        result = {
            'driver': __name__,
            'command': commandName,
            'output': output
        }

        if args:
            result['args'] = args

        return result

    def getCommandList(self):
        if not self.connected:
            self.connect()

        output = subprocess.check_output([self.executable, 'shell', 'pm', 'list',
            'packages', '-f']).split('\n')
        appList = []
        for line in output:
            pos = line.find('=')
            if pos > 0:
                appList.append({
                    'appName': line[pos + 1:],
                    'activity': []
                })

        for appInfo in appList:
            self.logger.debug("Processing %s app", appInfo['appName'])
            output = subprocess.check_output([self.executable, 'shell', 'pm',
                'dump', appInfo['appName']]).split('\n')
            for index, line in enumerate(output):
                if line.find('MAIN') > 0:
                    activityLine = output[index - 1]
                    pos = activityLine.find(appInfo['appName'] + '/')
                    if pos > 0:
                        appInfo['activity'].append(activityLine[
                            activityLine.find('/', pos) + 1:activityLine.find(' ', pos)])

        return appList
