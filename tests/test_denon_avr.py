import unittest
from unittest.mock import Mock
import yaml

from drivers.denon_avr import DenonAVR


class UtilsTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.load(configFile)

    def test_simple(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=bytearray())
        driver.connected = True
        driver.sendCommandRaw('command1', config['commands']['command1'])
        driver.conn.send.assert_called_with('VL\r\n'.encode())

    def test_send_with_args(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=bytearray())
        driver.connected = True
        driver.sendCommandRaw('command1', config['commands']['command1'], '12')
        driver.conn.send.assert_called_with('VL12\r\n'.encode())

    def test_send_float_even(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=bytearray())
        driver.connected = True
        driver.sendCommandRaw('command3', config['commands']['command3'], '12')
        driver.conn.send.assert_called_with('MV12\r\n'.encode())

    def test_send_float_fract(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=bytearray())
        driver.connected = True
        driver.sendCommandRaw('command3', config['commands']['command3'], '12.0')
        driver.conn.send.assert_called_with('MV12\r\n'.encode())

    def test_send_with_args_decimal(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        driver.conn = Mock()
        driver.conn.recv = Mock(return_value=bytearray())
        driver.connected = True
        driver.sendCommandRaw('command1', config['commands']['command1'], '12.5')
        driver.conn.send.assert_called_with('VL125\r\n'.encode())

    def test_output_simple(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'VL12' ] }
        driver.process_result('command1', config['commands']['command1'], result)
        self.assertEqual(result['result'], '12')

    def test_output_multiline(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'VL13', 'VL14', 'VL12' ] }
        driver.process_result('command1', config['commands']['command1'], result)
        self.assertEqual(result['result'], '12')

    def test_output_with_translate(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'MPWRUP' ] }
        driver.process_result('command2', config['commands']['command2'], result)
        self.assertEqual(result['result'], 'up')

    def test_output_multiple_matches_translate(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'MPWR12', 'MPWRON', 'MPWRUP' ] }
        driver.process_result('command2', config['commands']['command2'], result)
        self.assertEqual(result['result'], 'up')

    def test_output_multiple_matches_numeric(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'MPWRUP', 'MPWRON', 'MPWR12' ] }
        driver.process_result('command4', config['commands']['command4'], result)
        self.assertEqual(result['result'], '12')

    def test_output_volume_whole(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'MV12' ] }
        driver.process_result('current_volume', config['commands']['current_volume'], result)
        self.assertEqual(result['result'], 12)

    def test_output_volume_half(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'MV125' ] }
        driver.process_result('current_volume', config['commands']['current_volume'], result)
        self.assertEqual(result['result'], 12.5)

    def test_output_volume_multi_line(self):
        config = UtilsTester.config['denon']
        driver = DenonAVR(config, Mock())
        result = { 'output': [ 'MV15', 'MVMAX80', 'MV12', 'MVMAX80' ] }
        driver.process_result('current_volume', config['commands']['current_volume'], result)
        self.assertEqual(result['result'], 12)

if __name__ == '__main__':
    unittest.main()
