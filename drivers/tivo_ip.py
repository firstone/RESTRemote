import socket
import time

from drivers.base_driver import BaseDriver


class TivoIP(BaseDriver):

    RECEIVE_BUFFER_SIZE = 1024

    def __init__(self, config, logger, use_numeric_key=False):
        super(TivoIP, self).__init__(config, logger, use_numeric_key)

        logger.info('Loaded %s driver', self.__class__.__name__)
        self.conn = None

    def connect(self):
        self.do_connect()
        self.connected = True
        self.close()
        
    def do_connect(self):
        if self.conn is not None:
            return

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.config['hostName'], self.config['port']))
        self.conn.settimeout(self.config['timeout'])

    def close(self):
        self.conn.close()
        self.conn = None

    def sendCommandRaw(self, commandName, command, args=None):
        result = ''
        try:
            self.do_connect()
            if (command.get('argument') or 'value_set' in command) and args:
                for digit in str(args):
                    self.conn.send(f'{command["code"]} NUM{digit}\r\n'.encode())
            else:
                self.conn.send(f'{command["code"]}\r\n'.encode())

            if command.get('response', False):
                result = self.conn.recv(TivoIP.RECEIVE_BUFFER_SIZE).decode()
            delay = command.get('delay')
            if delay:
                time.sleep(delay)
        except socket.timeout:
            pass

        if not command.get('has_more', False):
            self.close()

        return result
