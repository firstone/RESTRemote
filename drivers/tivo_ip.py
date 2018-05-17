import socket
import time

from drivers.base_driver import BaseDriver


class TivoIP(BaseDriver):

    RECEIVE_BUFFER_SIZE = 1024

    def __init__(self, config, logger, use_numeric_key=False):
        super(TivoIP, self).__init__(config, logger, use_numeric_key)

        logger.info('Loaded %s driver', __name__)

    def connect(self):
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((self.config['hostName'], self.config['port']))
        conn.settimeout(self.config['timeout'])
        conn.close()
        self.connected = True

    def sendCommandRaw(self, commandName, command, args=None):
        result = ''
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((self.config['hostName'], self.config['port']))
            conn.settimeout(self.config['timeout'])
            conn.send(command['code'].encode())
            if (command.get('argument') or 'value_set' in command) and args:
                conn.send(args.encode())
            conn.send('\r\n'.encode())
            if command.get('response', False):
                result = conn.recv(TivoIP.RECEIVE_BUFFER_SIZE).decode()
            delay = command.get('delay')
            if delay:
                time.sleep(delay)
        except socket.timeout:
            pass
        conn.close()
        return result
