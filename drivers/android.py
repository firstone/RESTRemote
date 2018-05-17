import subprocess

from drivers.base_driver import BaseDriver


class Android(BaseDriver):

    ACTIVITY_RECORD = 'ActivityRecord'

    def __init__(self, config, logger, use_numeric_key=False):
        super(Android, self).__init__(config, logger, use_numeric_key)

        self.executable = config['executable']

        logger.info('Loaded %s driver', __name__)

    def connect(self):
        self.logger.debug('ADB status %s', subprocess.check_output(
            [self.executable, 'connect', self.connectionDescription]).decode())
        output = subprocess.check_output([self.executable, 'devices']).decode().split('\n')
        for line in output:
            if line.startswith(self.connectionDescription):
                if line.split('\t')[1] == 'device':
                    self.connected = True
                    return

        raise IOError('Connection to ' + self.connectionDescription +
            ' failed. If device is accessible, try restarting it')

    def sendCommandRaw(self, commandName, command, args=None):
        if not self.connected:
            self.connect()

        if commandName == 'start_app':
            result = subprocess.check_output([self.executable, 'shell', 'am',
                'start', '-n', args]).decode()
        elif commandName == 'get_app_list':
            result = self.getCommandList()
        elif commandName == 'get_current_activity':
            result = self.getCurrentActivity()
        else:
            result = subprocess.check_output([self.executable, 'shell', 'input',
                'keyevent', str(self.config['commands'][commandName]['code'])]).decode()

        return result

    def getCurrentActivity(self):
        output = subprocess.check_output([self.executable, 'shell', 'dumpsys',
            'window', 'windows']).decode().split('\n')
        for line in output:
            pos = line.find('mFocusedApp')
            if pos > 0:
                pos = line.find(Android.ACTIVITY_RECORD)
                if pos > 0:
                    values = line[pos + len(Android.ACTIVITY_RECORD):].split(' ')
                    return values[2].split('/')[0]

        return ''

    def getCommandList(self):
        if not self.connected:
            self.connect()

        output = subprocess.check_output([self.executable, 'shell', 'pm', 'list',
            'packages', '-f']).decode().split('\n')
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
                'dump', appInfo['appName']]).decode().split('\n')
            for index, line in enumerate(output):
                if line.find('MAIN') > 0:
                    activityLine = output[index - 1]
                    pos = activityLine.find(appInfo['appName'] + '/')
                    if pos > 0:
                        appInfo['activity'].append(activityLine[
                            activityLine.find('/', pos) + 1:activityLine.find(' ', pos)])

        return appList
