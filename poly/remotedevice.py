import time

from polyinterface import LOGGER
from polyinterface import Node


class RemoteDevice(Node):

    def __init__(self, controller, primaryDevice, primary, address, driverName,
        deviceName, config, deviceDriver):
        super(RemoteDevice, self).__init__(controller, primary,
            address, deviceName)

        self.id = driverName

        self.driverSetters = {}
        self.suffix = config.get('suffix', '')
        self.prefix = config.get('prefix', '')
        for commandName in config.get('commands', {}).keys():
            self.commands[commandName] = RemoteDevice.execute_command

            polyData = config['poly'].get('commands', {}).get(commandName)
            if polyData and 'driver' in polyData:
                command = deviceDriver.getCommand(self.prefix + commandName + self.suffix)
                self.drivers.append({
                    'driver': polyData['driver']['name'],
                    'value': 0,
                    'uom': polyData.get('param', {}).get('uom', 25)
                })
                if command is not None and command.get('readOnly', False):
                    self.driverSetters[polyData['driver']['name']] = self.prefix + commandName + self.suffix
                elif 'input' in polyData['driver'] and deviceDriver.hasCommand(self.prefix + polyData['driver']['input'] + self.suffix):
                    self.driverSetters[polyData['driver']['name']] = self.prefix + polyData['driver']['input'] + self.suffix

        self.primaryDevice = primaryDevice
        self.deviceDriver = deviceDriver

    def execute_command(self, command):
        try:
            self.deviceDriver.executeCommand(self.prefix + command['cmd'] + self.suffix,
                command.get('value'))
            time.sleep(1)
            self.refresh_state()
        except:
            LOGGER.exception('Error sending command to ' + self.name)

    def refresh_state(self):
        if self.primaryDevice.connected:
            try:
                for driverName, commandName in self.driverSetters.items():
                    output = self.deviceDriver.getData(commandName)
                    result = output.get('result')
                    if result is not None:
                        self.setDriver(driverName, float(result))
            except:
                LOGGER.exception('Error refreshing ' + self.name + ' device state')
