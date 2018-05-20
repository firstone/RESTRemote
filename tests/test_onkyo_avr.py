import struct
import unittest
from unittest.mock import Mock
import yaml

from drivers.onkyo_avr import OnkyoAVR


class UtilsTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.load(configFile)

    def test_simple(self):
        config = UtilsTester.config['onkyo']
        driver = OnkyoAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=bytearray())
        driver.connected = True
        driver.sendCommandRaw('command1', config['commands']['command1'], '01')
        message = struct.Struct(">4sIIB3x8s")
        driver.conn.send.assert_called_with(message.pack('ISCP'.encode(), 16, 8,
            1, '!1MVL01\r'.encode()))

    def test_output(self):
        config = UtilsTester.config['onkyo']
        driver = OnkyoAVR(config, Mock())
        message = struct.Struct(">4sIIB3x8s")
        result = { 'output': message.pack('ISCP'.encode(), 16, 8, 1,
            '!1MVL0a\r'.encode()) }
        driver.process_result('command1', config['commands']['command1'], result)
        self.assertEqual(result['result'], 10)

if __name__ == '__main__':
    unittest.main()
