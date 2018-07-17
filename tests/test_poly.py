import sys
import unittest
from unittest.mock import Mock
from unittest.mock import MagicMock
import yaml

import polyinterface

from poly.remotedevice import RemoteDevice

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
polyinterface.LOGGER.handlers = []


class PolyTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.load(configFile)

    def test_simple(self):
        driver = Mock()
        primaryDevice = Mock()
        driver.getCommand = MagicMock(return_value=None)
        device = RemoteDevice(None, primaryDevice, None, None, None, "test device",
            PolyTester.config['simple'], driver)
        device.runCmd({'cmd': 'command1'})
        driver.executeCommand.assert_called_with('command1', None)

    def test_state(self):
        driver = Mock()
        driver.getData = Mock(return_value={ 'result': 1 })
        primaryDevice = Mock()
        driver.getCommand = MagicMock(return_value=None)
        primaryDevice.connected = True
        device = RemoteDevice(None, primaryDevice, None, None, None, "test device",
            PolyTester.config['state'], driver)
        device.runCmd({'cmd': 'command1'})
        driver.executeCommand.assert_called_with('command1', None)
        driver.getData.assert_called_with('command2')

    def test_suffix(self):
        driver = Mock()
        driver.getData = Mock(return_value={ 'result': 1 })
        primaryDevice = Mock()
        driver.getCommand = MagicMock(return_value=None)
        primaryDevice.connected = True
        device = RemoteDevice(None, primaryDevice, None, None, None, "test device",
            PolyTester.config['suffix']['commandGroups']['group1'], driver)
        device.runCmd({'cmd': 'command1'})
        driver.executeCommand.assert_called_with('command1_g1', None)
        driver.getData.assert_called_with('command2_g1')

    def test_prefix(self):
        driver = Mock()
        driver.getData = Mock(return_value={ 'result': 1 })
        primaryDevice = Mock()
        driver.getCommand = MagicMock(return_value=None)
        primaryDevice.connected = True
        device = RemoteDevice(None, primaryDevice, None, None, None, "test device",
            PolyTester.config['prefix']['commandGroups']['group1'], driver)
        device.runCmd({'cmd': 'command1'})
        driver.executeCommand.assert_called_with('g1_command1', None)
        driver.getData.assert_called_with('g1_command2')

    def test_skips_bad_input_command(self):
        driver = Mock()
        driver.getData = Mock(return_value={ 'result': 1 })
        driver.hasCommand = Mock(return_value=False)
        primaryDevice = Mock()
        driver.getCommand = MagicMock(return_value=None)
        primaryDevice.connected = True
        device = RemoteDevice(None, primaryDevice, None, None, None, "test device",
            PolyTester.config['state'], driver)
        device.runCmd({'cmd': 'command1'})
        driver.executeCommand.assert_called_with('command1', None)
        driver.getData.assert_not_called()

if __name__ == '__main__':
    unittest.main()
