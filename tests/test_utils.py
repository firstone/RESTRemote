import unittest
import yaml

import utils


class UtilsTester(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('tests/config.yaml', 'r') as configFile:
            cls.config = yaml.load(configFile)

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

if __name__ == '__main__':
    unittest.main()
