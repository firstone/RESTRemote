import socket
import time

from drivers.base_driver import BaseDriver
import utils


class DenonAVR(BaseDriver):

    BUF_SIZE = 4096
    RESPONSE_DELAY = .15
    CLOSE_DELAY = .15
    SEARCH_SUFFIX = '?'

    def __init__(self, config, logger, use_numeric_key=False):
        super(DenonAVR, self).__init__(config, logger, use_numeric_key)

        self.conn = None
        logger.info('Loaded %s driver', self.__class__.__name__)

    def is_connected(self):
        result = super(DenonAVR, self).is_connected()
        self.autoClose()

        return result

    def connect(self):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM,
            socket.IPPROTO_TCP)
        self.logger.debug("Connecting to %s:%s", self.config['hostName'],
            self.config['port'])
        self.conn.connect((self.config['hostName'], self.config['port']))
        self.conn.settimeout(self.config['timeout'])
        self.connected = True

    def autoClose(self):
        if self.config.get('connectOnDemand', False):
            self.conn.close()
            self.connected = False
            time.sleep(self.CLOSE_DELAY)

    def sendCommandRaw(self, commandName, command, args=None):
        if not self.connected:
            self.connect()

        result = ''
        try:
            commandStr = command['code']
            if args:
                if command.get('acceptsFloat', False):
                    commandStr += '{0:g}'.format(float(args)).replace('.', '')
                else:
                    commandStr += args
            self.logger.debug("%s sending %s", self.__class__.__name__, commandStr)
            commandStr += '\r\n'
            self.conn.send(commandStr.encode())
            time.sleep(self.RESPONSE_DELAY)
            result = self.conn.recv(self.BUF_SIZE).decode()
            self.autoClose()
            self.logger.debug("%s received %s", self.__class__.__name__,
                result.replace('\r', '\\r'))
        except socket.timeout:
            pass
        return result[:-1].split('\r') if result else [result]

    def process_result(self, commandName, command, result):
        if len(result) == 0:
            return

        if commandName.startswith('current_volume'):
            output = utils.get_last_output(command, result['output'],
                self.paramParser.value_sets, DenonAVR.SEARCH_SUFFIX)

            if output is None:
                return

            if len(output) > 2:
                output = output[:2] + '.5'
            else:
                output = output + '.0'
            output = float(output)
        else:
            output = self.paramParser.translate_param(command,
                utils.get_last_output(command, result['output'],
                    self.paramParser.value_sets, DenonAVR.SEARCH_SUFFIX))

        if output:
            result['result'] = output
