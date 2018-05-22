import importlib
from polyinterface import LOGGER
from polyinterface import Controller
import time
import utils

from poly.remotedevice import RemoteDevice
from poly.primaryremotedevice import PrimaryRemoteDevice


class RemoteController(Controller):

    def __init__(self, polyglot, config):
        super(RemoteController, self).__init__(polyglot)
        self.configData = config

    def start(self):
        LOGGER.info('Started %s Controller', self.id)
        # self.addNotice('Hello')
        # self.removeNotice(0)
        self.setDriver('ST', 1)
        self.discover()

    def shortPoll(self):
        for node in self.nodes.values():
            node.refresh_state()
        pass

    def longPoll(self):
        pass

    def query(self):
        pass

    def discover(self, *args, **kwargs):
        time.sleep(1)
        for deviceName, deviceData in self.configData['devices'].items():
            if deviceData.get('enable', True):
                driverName = deviceData['driver']
                deviceData.update(self.configData['drivers'][driverName])
                polyData = self.configData['poly']['drivers'].get(driverName, {})
                deviceData['poly'] = polyData

                driverModule = importlib.import_module('drivers.' + driverName)
                deviceDriver = getattr(driverModule,
                    deviceData.get('moduleName', driverName.capitalize()))(
                        utils.merge_commands(deviceData), LOGGER, True)

                nodeAddress = deviceData['poly_address']
                nodeName = deviceData.get('name', utils.name_to_desc(deviceName))
                primaryDevice = PrimaryRemoteDevice(self, nodeAddress,
                    driverName, nodeName, deviceData, deviceDriver)
                self.addNode(primaryDevice)
                for commandGroup, commandGroupData in deviceData.get(
                    'commandGroups', {}).items():
                    commandGroupData['poly'] = polyData
                    groupConfig = self.configData['poly']['commandGroups'].get(
                        commandGroup)
                    if groupConfig:
                        groupDriverName = driverName + '_' + commandGroup
                        groupNodeAddress = nodeAddress + '_' + groupConfig['address']
                        self.addNode(RemoteDevice(self, primaryDevice, nodeAddress,
                            groupNodeAddress, groupDriverName,
                                utils.name_to_desc(commandGroup),
                                commandGroupData, deviceDriver))

    def delete(self):
        pass

    def stop(self):
        pass

    def refresh_state(self):
        pass

    id = 'controller'
    commands = { 'DISCOVER': discover }
    drivers = [ { 'driver': 'ST', 'value': 0, 'uom': 2 } ]
