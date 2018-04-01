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
            for commandName, commandData in self.config['commands'].iteritems():
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
        if commandName == 'start_app':
            output = subprocess.check_output([self.executable, 'shell', 'am',
                'start', '-n', self.config['commands'][commandName]['values'][args]])
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
            print "Processing", appInfo['appName']
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
