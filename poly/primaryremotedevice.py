from polyinterface import LOGGER

from poly.remotedevice import RemoteDevice


class PrimaryRemoteDevice(RemoteDevice):

    drivers = [ {'driver': 'ST', 'value': 0, 'uom': 2} ]

    def __init__(self, controller, address, driverName, deviceName,
        config, deviceDriver):
        self.driverSetters = {}
        for commandName, commandData in config['poly'].get('commands', {}).items():
            if 'driver' in commandData:
                self.drivers.append({
                    'driver': commandData['driver']['name'],
                    'value': 0,
                    'uom': commandData.get('param', {}).get('uom', 25)
                })

            if 'set_driver' in commandData:
                self.driverSetters[commandData['set_driver']] = commandName

        super(PrimaryRemoteDevice, self).__init__(controller, address,
            address, driverName, deviceName, config, deviceDriver)

    def start(self):
        self.deviceDriver.start()
        self.refresh_state()

    def refresh_state(self):
        self.setDriver('ST', 1 if self.deviceDriver.is_connected() else 0)
        for driverName, commandName in self.driverSetters.items():
            output = self.deviceDriver.getData(commandName)
            result = output.get('result')
            if result is not None:
                self.setDriver(driverName, float(result))
