import struct
import unittest
from unittest.mock import Mock
import yaml

from drivers.onkyo_avr import OnkyoAVR


class UtilsTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.safe_load(configFile)

    def test_simple(self):
        response = 'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1MVL14\x1a\r\n'

        config = UtilsTester.config['onkyo']
        driver = OnkyoAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=response.encode())
        driver.connected = True
        driver.sendCommandRaw('command1', config['commands']['command1'], '01')
        message = struct.Struct(">4sIIB3x8s")
        driver.conn.send.assert_called_with(message.pack('ISCP'.encode(), 16, 8,
                                                         1, '!1MVL01\r'.encode()))

    def test_output(self):
        response = 'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1MVL14\x1a\r\n'
        config = UtilsTester.config['onkyo']
        driver = OnkyoAVR(config, Mock())
        result = {'output': response}
        driver.process_result(
            'command2', config['commands']['command2'], result)
        self.assertEqual(result['result'], 20)

    def test_long_response(self):
        response = (
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1MVL14\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1PWR01\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1ZPW00\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1PW301\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1PWR01\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1PW301\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1SLI23\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1ZPW00\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1AMT00\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1MVL2A\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1SL302\x1a\r\n'
            'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1SLI23\x1a\r\n'
        )

        config = UtilsTester.config['onkyo']
        driver = OnkyoAVR(config, Mock())
        result = {'output': response}
        driver.process_result(
            'command2', config['commands']['command2'], result)
        self.assertEqual(result['result'], 42)

    def test_na_response(self):
        response = 'ISCP\x00\x00\x00\x10\x00\x00\x00\x0b\x01\x00\x00\x00!1MVLN/A\x1a\r\n'
        config = UtilsTester.config['onkyo']
        driver = OnkyoAVR(config, Mock())
        result = {'output': response}
        driver.process_result(
            'command2', config['commands']['command2'], result)
        self.assertNotIn('result', result)


if __name__ == '__main__':
    unittest.main()
