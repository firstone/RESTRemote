import socket
import struct

from drivers.base_driver import BaseDriver


class OnkyoAVR(BaseDriver):

    ICSP_SIGNATURE = 'ICSP'
    ICSP_VERSION = 1
    ICSP_HEADER = struct.Struct(">4sIIB3x")
    DESTINATION_UNIT_TYPE = '!1'
    CMD_LEN = 3
    RESPONSE_DATA_OFFSET = ICSP_HEADER.size + len(DESTINATION_UNIT_TYPE) + CMD_LEN
    RECEIVE_BUFFER_SIZE = 1024

    def __init__(self, config, logger, use_numeric_key=False):
        super(OnkyoAVR, self).__init__(config, logger, use_numeric_key)

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
                commandStr += args
            request = self.convert_to_ISCP(commandStr)
            print("Onkyo sending", request)
            self.conn.send(self.convert_to_ISCP(commandStr))
            result = self.conn.recv(OnkyoAVR.RECEIVE_BUFFER_SIZE).decode()
            print("Onkyo received", result)
        except socket.timeout:
            pass
        return result

    def convert_to_ISCP(self, strData):
        strData = OnkyoAVR.DESTINATION_UNIT_TYPE + strData + '\r'
        data = OnkyoAVR.ICSP_HEADER.pack(OnkyoAVR.ICSP_SIGNATURE.encode(),
            OnkyoAVR.ICSP_HEADER.size, len(strData), OnkyoAVR.ICSP_VERSION)
        return data + strData.encode()

    def process_result(self, commandName, command, result):
        if len(result['output']) == 0:
            return

        result['output'] = result['output'][OnkyoAVR.RESPONSE_DATA_OFFSET:OnkyoAVR.RESPONSE_DATA_OFFSET + 2]
        super(OnkyoAVR, self).process_result(commandName, command, result)
