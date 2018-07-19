import pychromecast

from drivers.base_driver import BaseDriver
import utils


class Chromecast(BaseDriver):

    PLAYLISTS_KEY_NAME = 'chromecastPlaylists'

    CAST_LIST = {}

    def __init__(self, config, logger, use_numeric_key=False):
        super(Chromecast, self).__init__(config, logger, use_numeric_key)

        self.cast = None

        logger.info('Loaded %s driver', self.__class__.__name__)

    def sendCommandRaw(self, commandName, command, args=None):
        attr = None

        if 'mediaCode' in command:
            attr = getattr(self.cast.media_controller, command['mediaCode'])
        else:
            attr = getattr(self.cast, command['code'])

        if command.get('result', False):
            result = getattr(attr, command['argKey'])
            return result
        elif args is not None:
            attr(*args)
        else:
            attr()
        return ''

    def connect(self):
        if self.cast is None:
            Chromecast.discoverDevices(None)

            self.cast = Chromecast.CAST_LIST.get(self.config['name'])

        if self.cast:
            if not self.cast.socket_client.is_connected:
                self.cast.socket_client.initialize_connection()

            self.connected = self.cast.socket_client.is_connected

    @staticmethod
    def processParams(config, param):
        playlists = param.get(Chromecast.PLAYLISTS_KEY_NAME)
        if playlists is None:
            return False

        values = []
        for playlist in playlists:
            values.append({
                'value': playlist['name'],
                'param': [ playlist['url'], playlist['type'] ]
            })
        config.setdefault('values', {})
        if config['values'].get(Chromecast.PLAYLISTS_KEY_NAME) == values:
            return False

        config['values'][Chromecast.PLAYLISTS_KEY_NAME] = values
        return True

    @staticmethod
    def discoverDevices(config):
        if len(Chromecast.CAST_LIST) == 0:
            casts = pychromecast.get_chromecasts()

            for cast in casts:
                friendly_name = cast.device.friendly_name
                Chromecast.CAST_LIST[friendly_name] = cast

        result = {}
        for name in Chromecast.CAST_LIST.keys():
            result[utils.desc_to_name(name)] = {
                'name': name,
                'driver': 'chromecast'
            }

        return result
