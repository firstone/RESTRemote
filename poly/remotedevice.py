from polyinterface import Node


class RemoteDevice(Node):

    def __init__(self, controller, primary, address, driverName, deviceName,
        config, deviceDriver):
        self.id = driverName
        for commandName in config.get('commands', {}).keys():
            self.commands[commandName] = RemoteDevice.execute_command

        super(RemoteDevice, self).__init__(controller, primary,
            address, deviceName)

        self.deviceDriver = deviceDriver

    def query(self):
        pass

    def execute_command(self, command):
        self.deviceDriver.executeCommand(command['cmd'], command.get('value'))
        self.refresh_state()

    def refresh_state(self):
        pass
