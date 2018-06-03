import importlib
from polyinterface import LOGGER
from polyinterface import Controller
import time
import utils

from poly.remotedevice import RemoteDevice
from poly.primaryremotedevice import PrimaryRemoteDevice


class RemoteController(Controller):

    def __init__(self, polyglot, config, has_devices=False):
        super(RemoteController, self).__init__(polyglot)
        self.configData = config
        self.has_devices = has_devices

    def start(self):
        LOGGER.info('Started %s Controller', self.id)

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

    def processParams(self, config):
        params = {}
        devicesConfig = {}
        for driverName, driverData in self.configData['drivers'].items():
            paramName = driverName + '_count'
            if paramName not in config:
                params[paramName] = 0
            else:
                for i in range(0, int(config[paramName])):
                    deviceConfig = {}
                    deviceName = driverName + "_" + str(i)
                    for param in driverData['parameters']:
                        paramName = deviceName + "_" + param['name']
                        if paramName not in config:
                            params[paramName] = param['default']
                        else:
                            deviceConfig[param['name']] = config[paramName]
                    deviceConfig['driver'] = driverName
                    devicesConfig[deviceName] = deviceConfig

        self.configData['devices'] = devicesConfig
        return params

    def isDeviceConfigured(self, device):
        for param in self.configData['drivers'][device['driver']]['parameters']:
            if param.get('required', False) and (device[param['name']] == 0 or
                device[param['name']] == '0' or device[param['name']] == ''):
                return False
        return True

    def getDeviceAddress(self, deviceName, addressMap):
        address = addressMap.get(deviceName)
        if not address:
            address = "d_" + str(len(addressMap))
            addressMap[deviceName] = address

        return address

    def discover(self, *args, **kwargs):
        time.sleep(1)

        addressMap = self.polyConfig.get('customData', {}).get('addressMap', {})
        if not self.has_devices:
            customParams = self.processParams(self.polyConfig.get('customParams', {}))
            if len(customParams) > 0:
                self.addCustomParam(customParams)

        for deviceName, deviceData in self.configData['devices'].items():
            if self.isDeviceConfigured(deviceData) and deviceData.get('enable', True):
                driverName = deviceData['driver']
                deviceData.update(self.configData['drivers'][driverName])
                polyData = self.configData['poly']['drivers'].get(driverName, {})
                deviceData['poly'] = polyData

                driverModule = importlib.import_module('drivers.' + driverName)
                deviceDriver = getattr(driverModule,
                    deviceData.get('moduleName', driverName.capitalize()))(
                        utils.merge_commands(deviceData), LOGGER, True)

                nodeAddress = self.getDeviceAddress(deviceName, addressMap)
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
                        groupNodeAddress = self.getDeviceAddress(
                            deviceName + '_' + commandGroup, addressMap)
                        self.addNode(RemoteDevice(self, primaryDevice, nodeAddress,
                            groupNodeAddress, groupDriverName,
                                utils.name_to_desc(commandGroup),
                                commandGroupData, deviceDriver))

        self.saveCustomData({'addressMap': addressMap})

    def delete(self):
        pass

    def stop(self):
        pass

    def refresh_state(self):
        pass

    id = 'controller'
    commands = { 'DISCOVER': discover }
    drivers = [ { 'driver': 'ST', 'value': 0, 'uom': 2 } ]
