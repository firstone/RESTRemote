from poly.remotedevice import RemoteDevice


class PrimaryRemoteDevice(RemoteDevice):

    drivers = [ {'driver': 'ST', 'value': 0, 'uom': 2} ]

    def __init__(self, controller, address, driverName, deviceName,
        config, deviceDriver):
        super(PrimaryRemoteDevice, self).__init__(controller, self, address,
            address, driverName, deviceName, config, deviceDriver)
        self.connected = False

    def start(self):
        self.deviceDriver.start()
        self.refresh_state()

    def refresh_state(self):
        self.connected = self.deviceDriver.is_connected()
        self.setDriver('ST', 1 if self.connected else 0)
        super(PrimaryRemoteDevice, self).refresh_state()
