import socket
import struct

from drivers.base_driver import BaseDriver
import utils


class OnkyoAVR(BaseDriver):

    ISCP_SIGNATURE = 'ISCP'
    ISCP_VERSION = 1
    ISCP_HEADER = struct.Struct(">4sIIB3x")
    DESTINATION_UNIT_TYPE = '!1'
    CMD_LEN = 3
    RESPONSE_DATA_OFFSET = ISCP_HEADER.size + len(DESTINATION_UNIT_TYPE) + CMD_LEN
    RECEIVE_BUFFER_SIZE = 1024
    SEARCH_SUFFIX = 'QSTN'

    def __init__(self, config, logger, use_numeric_key=False):
        super(OnkyoAVR, self).__init__(config, logger, use_numeric_key)

        logger.info('Loaded %s driver', self.__class__.__name__)

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
            self.logger.debug("%s sending %s", self.__class__.__name__, request)
            self.conn.send(self.convert_to_ISCP(commandStr))
            resultBuf = self.conn.recv(OnkyoAVR.RECEIVE_BUFFER_SIZE)
            self.logger.debug("%s received %s", self.__class__.__name__, resultBuf)
            result = resultBuf.decode()
        except socket.timeout:
            pass

        return result

    def convert_to_ISCP(self, strData):
        strData = OnkyoAVR.DESTINATION_UNIT_TYPE + strData + '\r'
        data = OnkyoAVR.ISCP_HEADER.pack(OnkyoAVR.ISCP_SIGNATURE.encode(),
            OnkyoAVR.ISCP_HEADER.size, len(strData), OnkyoAVR.ISCP_VERSION)
        return data + strData.encode()

    def process_result(self, commandName, command, result):
        if len(result['output']) == 0:
            return

        resultBuf = result['output'].encode()
        results = []
        while len(resultBuf) > 0:
            try:
                (_, _, responseLen, _) = OnkyoAVR.ISCP_HEADER.unpack(
                    resultBuf[:OnkyoAVR.ISCP_HEADER.size])
                # strip first 2 chars last 3 chars for \x1a\r\n
                results.append(resultBuf[OnkyoAVR.ISCP_HEADER.size + len(OnkyoAVR.DESTINATION_UNIT_TYPE):OnkyoAVR.ISCP_HEADER.size + responseLen - 3].decode())
                resultBuf = resultBuf[OnkyoAVR.ISCP_HEADER.size + responseLen:]
            except:
                self.logger.error("Error processing buffer. "
                    "Possibly incomplete buffer. Increase receive buffer size")
                break

        result['output'] = utils.get_last_output(command, results,
            self.paramParser.value_sets, OnkyoAVR.SEARCH_SUFFIX)

        super(OnkyoAVR, self).process_result(commandName, command, result)
