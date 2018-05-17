import socket
import time

from drivers.base_driver import BaseDriver


class DenonAVR(BaseDriver):

    BUF_SIZE = 4096
    RESPONSE_DELAY = 1

    def __init__(self, config, logger, use_numeric_key=False):
        super(DenonAVR, self).__init__(config, logger, use_numeric_key)

        logger.info('Loaded %s driver', __name__)

    def connect(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.config['hostName'], self.config['port']))
        self.conn.settimeout(self.config['timeout'])
        self.connected = True

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
            commandStr += '\n'
            self.conn.send(commandStr.encode())
            time.sleep(self.RESPONSE_DELAY)
            result = self.conn.recv(self.BUF_SIZE).decode()
        except socket.timeout:
            pass
        return result[:-1].split('\r') if result else result

    def process_result(self, commandName, command, result):
        if len(result) == 0:
            return

        if commandName.startswith('current_volume'):
            output = self.get_last_output(command, result['output'])
            if len(output) > 2:
                output = output[:2] + '.5'
            else:
                output = output + '.0'
            output = float(output)
        else:
            output = self.paramParser.translate_param(command,
                self.get_last_output(command, result['output']))

        if output:
            result['result'] = output

    def get_last_output(self, command, output):
        prefix = command['code'].replace('?', '')
        keys = self.paramParser.value_sets.get(command.get('value_set', ''), {})
        output.reverse()

        for line in output:
            if line.startswith(prefix):
                value = line[len(prefix):]
                if (command.get('acceptsNumber', False) or
                    command.get('acceptsFloat', False) or
                    command.get('acceptsHex', False)):
                    try:
                        float(value)
                        return value
                    except:
                        pass
                elif keys.get(value) is not None:
                    return value

        return ''
