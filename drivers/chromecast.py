import pychromecast

from drivers.base_driver import BaseDriver
import utils


class Chromecast(BaseDriver):

    PLAYLISTS_KEY_NAME = 'chromecastPlaylists'

    def __init__(self, config, logger, use_numeric_key=False):
        super(Chromecast, self).__init__(config, logger, use_numeric_key)

        self.media_controller = None

        logger.info('Loaded %s driver', self.__class__.__name__)

    def sendCommandRaw(self, commandName, command, args=None):
        attr = getattr(self.media_controller, command['code'])
        if command.get('result', False):
            result = getattr(attr, command['argKey'])
            return result
        elif args is not None:
            attr(*args)
        else:
            attr()
        return ''

    def connect(self):
        self.connected = False
        if self.media_controller is None:
            casts = pychromecast.get_chromecasts()
            for cast in casts:
                if cast.device.friendly_name == self.config['name']:
                    self.media_controller = cast.media_controller
                    self.connected = True
                    return

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
        result = {}
        casts = pychromecast.get_chromecasts()
        for cast in casts:
            friendly_name = cast.device.friendly_name
            result[utils.desc_to_name(friendly_name)] = {
                'name': friendly_name,
                'driver': 'chromecast'
            }

        return result
