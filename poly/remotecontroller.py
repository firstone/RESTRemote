import copy
import importlib
from polyinterface import LOGGER
from polyinterface import Controller
import time
import utils

from polyprofile import ProfileFactory
from poly.primaryremotedevice import PrimaryRemoteDevice
from poly.remotedevice import RemoteDevice


class RemoteController(Controller):

    def __init__(self, polyglot, config, has_devices=False):
        super(RemoteController, self).__init__(polyglot)
        self.configData = config
        self.has_devices = has_devices
        self.deviceDrivers = {}
        self.deviceDriverInstances = {}
        self.poly.onConfig(self.process_config)
        self.currentConfig = None
        time.sleep(1)
        self.createDevices()

    def process_config(self, config):
        self.remove_stale_nodes(config)

        typedConfig = config.get('typedCustomData')
        if self.currentConfig != typedConfig:
            self.currentConfig = typedConfig
            needChanges = False
            devicesConfig = self.configData.get('devices', {})
            for driverName, paramList in typedConfig.items():
                if driverName in self.configData['drivers']:
                    for index, params in enumerate(paramList):
                        params['driver'] = driverName
                        devicesConfig[driverName + '_' + str(100 - index)] = params
                else:
                    for deviceDriverName, driverData in self.configData['drivers'].items():
                        if self.get_device_driver(deviceDriverName, driverData).processParams(
                            driverData, { driverName: paramList }):
                            needChanges = True
                            for deviceDriver in self.deviceDriverInstances[deviceDriverName]:
                                deviceDriver.configure(driverData)

            if needChanges:
                LOGGER.debug('Regenerating profile')
                factory = ProfileFactory('.', self.configData)
                factory.create()
                if factory.write():
                    LOGGER.debug('Profile has changed. Updating')
                    self.poly.installprofile()
                else:
                    LOGGER.debug('Profile not changed. Skipping')

            self.configData['devices'] = devicesConfig

    def remove_stale_nodes(self, config):
        # Remove node not present in config
        existingNodes = {}
        for node in config['nodes']:
            existingNodes[node['address']] = 1

        staleNodes = {}
        for nodeAddress, node in self.nodes.items():
            if nodeAddress not in existingNodes:
                staleNodes[nodeAddress] = 1

        customData = self.polyConfig.get('customData', {})
        addressMap = customData.get('addressMap', {})
        discoveredDevices = copy.deepcopy(customData.get('discoveredDevices', {}))

        for nodeAddress in staleNodes.keys():
            LOGGER.debug('Removing stale node ' + nodeAddress)
            for deviceName, deviceAddress in addressMap.items():
                if deviceAddress == nodeAddress:
                    del discoveredDevices[deviceName]
            del self.nodes[nodeAddress]

        if customData.get('discoveredDevices') != discoveredDevices:
            self.saveCustomData({
                'addressMap': addressMap,
                'discoveredDevices': discoveredDevices
            })

    def start(self):
        params = []
        for driverName, driverData in self.configData['drivers'].items():
            values = driverData.get('parameters')
            if values:
                param = {
                    'name': driverName,
                    'title': driverData.get('description', ''),
                    'isList': True,
                    'params': values
                }
                params.append(param)
            params.extend(driverData.get('driverParameters', []))
        self.poly.save_typed_params(params)

        self.setDriver('ST', 1)

    def shortPoll(self):
        for node in self.nodes.values():
            node.refresh_state()

    def longPoll(self):
        pass

    def refresh_state(self):
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
                            params[paramName] = param['defaultValue']
                        else:
                            deviceConfig[param['name']] = config[paramName]
                    deviceConfig['driver'] = driverName
                    devicesConfig[deviceName] = deviceConfig

        self.configData['devices'] = devicesConfig
        return params

    def isDeviceConfigured(self, device):
        for param in self.configData['drivers'][device['driver']].get('parameters', []):
            if param.get('isRequired', False) and (device[param['name']] == 0 or
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
        customData = self.polyConfig.get('customData', {})
        addressMap = customData.get('addressMap', {})
        discoveredDevices = copy.deepcopy(customData.get('discoveredDevices', {}))

        for driverName, driverData in self.configData['drivers'].items():
            devices = self.get_device_driver(driverName,
                driverData).discoverDevices(driverData)
            if devices is not None:
                discoveredDevices.update(devices)

        LOGGER.debug('Finished device discovery')
        self.saveCustomData({
            'addressMap': addressMap,
            'discoveredDevices': discoveredDevices
        })
        self.createDevices()

    def createDevices(self):
        customData = self.polyConfig.get('customData', {})
        addressMap = copy.deepcopy(customData.get('addressMap', {}))
        discoveredDevices = customData.get('discoveredDevices')

        devicesConfig = self.configData.get('devices', {})
        if discoveredDevices is not None:
                devicesConfig.update(discoveredDevices)

        self.configData['devices'] = devicesConfig
        for deviceName, deviceData in devicesConfig.items():
            if self.isDeviceConfigured(deviceData) and deviceData.get('enable', True):
                driverName = deviceData['driver']
                deviceData.update(self.configData['drivers'][driverName])
                polyData = self.configData['poly']['drivers'].get(driverName, {})
                deviceData['poly'].update(polyData)

                deviceDriver = self.get_device_driver(driverName, deviceData)(
                        utils.merge_commands(deviceData), LOGGER, True)
                self.deviceDriverInstances[driverName].append(deviceDriver)

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

        if customData.get('addressMap') != addressMap:
            self.saveCustomData({
                'addressMap': addressMap,
                'discoveredDevices': discoveredDevices
            })

    def get_device_driver(self, driverName, deviceData):
        deviceDriver = self.deviceDrivers.get(driverName)
        if deviceDriver is None:
            driverModule = importlib.import_module('drivers.' + driverName)
            deviceDriver = getattr(driverModule,
                deviceData.get('moduleName', driverName.capitalize()))
            self.deviceDrivers[driverName] = deviceDriver
            self.deviceDriverInstances[driverName] = []

        return deviceDriver

    id = 'controller'
    commands = { 'DISCOVER': discover }
    drivers = [ { 'driver': 'ST', 'value': 0, 'uom': 2 } ]
