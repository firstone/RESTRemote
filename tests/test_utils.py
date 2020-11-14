import unittest
import yaml

import utils


class UtilsTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.safe_load(configFile)

    def test_simple(self):
        config = UtilsTester.config['simple']
        utils.flatten_commands(config)
        self.assertEqual(len(list(config['commands'].keys())), 2)

    def test_sub_group(self):
        config = UtilsTester.config['sub_group']
        utils.flatten_commands(config)
        self.assertEqual(len(list(config['commands'].keys())), 3)

    def test_no_main(self):
        config = UtilsTester.config['no_main']
        utils.flatten_commands(config)
        self.assertEqual(len(list(config['commands'].keys())), 1)

    def test_suffix(self):
        config = UtilsTester.config['suffix']
        utils.flatten_commands(config)
        self.assertTrue('command1_g1' in config['commands'])
        self.assertTrue('command2_g1' in config['commands'])

    def test_prefix(self):
        config = UtilsTester.config['prefix']
        utils.flatten_commands(config)
        self.assertTrue('g1_command1' in config['commands'])
        self.assertTrue('g1_command2' in config['commands'])

    def test_last_output_number(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['intCommand'],
                                       ['cmd123'], {}, '')
        self.assertEqual(output, '123')

    def test_last_output_number_multi_line(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['intCommand'],
                                       ['cmd123', 'cmd234'], {}, '')
        self.assertEqual(output, '234')

    def test_last_output_number_multi_prefix(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['intCommand'],
                                       ['cmd123', 'cmdn234'], {}, '')
        self.assertEqual(output, '123')

    def test_last_output_float(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['floatCommand'],
                                       ['cmd123'], {}, '')
        self.assertEqual(output, '123')

    def test_last_output_float_multi_line(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['floatCommand'],
                                       ['cmd123', 'cmd234'], {}, '')
        self.assertEqual(output, '234')

    def test_last_output_hex(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['hexCommand'],
                                       ['cmdcaca'], {}, '')
        self.assertEqual(output, 'caca')

    def test_last_output_hex_multi_line(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['hexCommand'],
                                       ['cmdbaba', 'cmdcaca'], {}, '')
        self.assertEqual(output, 'caca')

    def test_last_output_values(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['valueCommand'],
                                       ['cmdkey1'], config['values'], '')
        self.assertEqual(output, 'key1')

    def test_last_output_values_multi_line(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['valueCommand'],
                                       ['cmd123', 'cmdkey1'], config['values'], '')
        self.assertEqual(output, 'key1')

    def test_last_output_suffix(self):
        config = UtilsTester.config['last_output']
        output = utils.get_last_output(config['commands']['suffixCommand'],
                                       ['cmd123'], {}, 'n')
        self.assertEqual(output, '123')


if __name__ == '__main__':
    unittest.main()
