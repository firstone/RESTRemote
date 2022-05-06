import copy
import unittest
from unittest.mock import call, MagicMock
import yaml

from drivers.base_driver import BaseDriver


class UtilsTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.safe_load(configFile)

    def test_simple(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        self.assertEqual(len(driver.getData('commands')['commands']), 7)

    def test_execute_command(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('command1')
        driver.sendCommandRaw.assert_called_with('command1',
                                                 config['commands']['command1'], None)

    def test_execute_command_list(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('command7')
        sub_command = copy.deepcopy(config['commands']['command7']['commands'][0])
        sub_command['has_more'] = True
        driver.sendCommandRaw.assert_has_calls([
            call('command7', sub_command, None),
            call('command7', config['commands']['command7']['commands'][1], None)
        ])

    def test_execute_command_with_arg_no_translate(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('command1', 'arg')
        driver.sendCommandRaw.assert_called_with('command1',
                                                 config['commands']['command1'], 'arg')

    def test_execute_command_with_arg_translate_failed(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('command2', 'arg')
        driver.sendCommandRaw.assert_called_with('command2',
                                                 config['commands']['command2'], 'arg')

    def test_execute_command_translate(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('command2', 'key1')
        driver.sendCommandRaw.assert_called_with('command2',
                                                 config['commands']['command2'], 'value1')

    def test_execute_command_translate_numberic(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None, True)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('command2', '0')
        driver.sendCommandRaw.assert_called_with('command2',
                                                 config['commands']['command2'], 'value1')

    def test_get_data_no_translate(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='some_value')

        response = driver.getData('command3')
        self.assertEqual(response['output'], 'some_value')
        self.assertNotIn('result', response)
        driver.sendCommandRaw.assert_called_with('command3',
                                                 config['commands']['command3'])

    def test_get_data_translate_failed(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='some_value')

        response = driver.getData('command4')
        self.assertEqual(response['output'], 'some_value')
        self.assertNotIn('result', response)
        driver.sendCommandRaw.assert_called_with('command4',
                                                 config['commands']['command4'])

    def test_get_data_translate_default(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='some_value')

        response = driver.getData('command6')
        self.assertEqual(response['output'], 'some_value')
        self.assertEqual(response['result'], 'key6')
        driver.sendCommandRaw.assert_called_with('command6',
                                                 config['commands']['command6'])

    def test_get_data_translate(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='value1')

        response = driver.getData('command4')
        self.assertEqual(response['output'], 'value1')
        self.assertEqual(response['result'], 'key1')
        driver.sendCommandRaw.assert_called_with('command4',
                                                 config['commands']['command4'])

    def test_get_data_translate_one_way(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='value3')

        response = driver.getData('command5')
        self.assertEqual(response['output'], 'value3')
        self.assertEqual(response['result'], 'key3')
        driver.sendCommandRaw.assert_called_with('command5',
                                                 config['commands']['command5'])

    def test_get_data_translate_numeric(self):
        config = UtilsTester.config['driver']
        driver = BaseDriver(config, None, True)
        driver.sendCommandRaw = MagicMock(return_value='value1')

        response = driver.getData('command4')
        self.assertEqual(response['output'], 'value1')
        self.assertEqual(response['result'], '0')
        driver.sendCommandRaw.assert_called_with('command4',
                                                 config['commands']['command4'])

    def test_execute_command_bool_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('boolCommand', 'on')
        driver.sendCommandRaw.assert_called_with('boolCommand',
                                                 config['commands']['boolCommand'], True)

    def test_execute_command_bool_param_translate(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('boolCommandTranslate', '1')
        driver.sendCommandRaw.assert_called_with('boolCommandTranslate',
                                                 config['commands']['boolCommandTranslate'], True)

    def test_execute_command_int_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock()

        driver.executeCommand('intCommand', '123')
        driver.sendCommandRaw.assert_called_with('intCommand',
                                                 config['commands']['intCommand'], 123)

    def test_execute_command_hex_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='0')

        driver.executeCommand('hexCommand', '11')
        driver.sendCommandRaw.assert_called_with('hexCommand',
                                                 config['commands']['hexCommand'], 'B')

    def test_execute_command_float_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='0')

        driver.executeCommand('floatCommand', '1.1')
        driver.sendCommandRaw.assert_called_with('floatCommand',
                                                 config['commands']['floatCommand'], '1.1')

    def test_execute_command_float_param_no_fract(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='0')

        driver.executeCommand('floatCommand', '1')
        driver.sendCommandRaw.assert_called_with('floatCommand',
                                                 config['commands']['floatCommand'], '1')

    def test_get_data_int_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='123')

        response = driver.getData('intResult')
        self.assertEqual(response['result'], 123)

    def test_get_data_hex_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='12')

        response = driver.getData('hexResult')
        self.assertEqual(response['result'], 18)

    def test_get_data_float_param(self):
        config = UtilsTester.config['numberParams']
        driver = BaseDriver(config, None)
        driver.sendCommandRaw = MagicMock(return_value='1.2')

        response = driver.getData('floatResult')
        self.assertEqual(response['result'], 1.2)


if __name__ == '__main__':
    unittest.main()
