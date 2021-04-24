import pychromecast
from pychromecast.discovery import stop_discovery
from zeroconf import Zeroconf

from drivers.base_driver import BaseDriver
import utils


class Chromecast(BaseDriver):

    APPS_KEY_NAME = 'chromecastApps'
    PLAYLISTS_KEY_NAME = 'chromecastPlaylists'
    ENABLED_KEY_NAME = 'enableChromecastSupport'
    CAST_LIST = {}
    CAST_CONNECT_TRIES = 1

    enabled = False

    def __init__(self, config, logger, use_numeric_key=False):
        super(Chromecast, self).__init__(config, logger, use_numeric_key)

        self.cast = None

        logger.info('Loaded %s driver', self.__class__.__name__)

    def sendCommandRaw(self, commandName, command, args=None):
        if commandName == 'start_app':
            if args == '':
                return ''
            elif not args:
                return self.sendCommandRaw('quit_app',
                                           self.config['commands']['quit_app'])
        elif commandName == 'toggle_mute':
            currentMute = self.sendCommandRaw('current_mute',
                                              self.config['commands']['current_mute'])
            return self.sendCommandRaw('set_mute',
                                       self.config['commands']['set_mute'], not currentMute)

        controllerName = command.get('controller')
        controller = getattr(
            self.cast, controllerName) if controllerName else self.cast
        attr = getattr(controller, command['code'])

        try:
            if command.get('result', False):
                result = getattr(attr, command['argKey'], '')
                return result
            elif args is not None:
                if type(args) == list:
                    attr(*args)
                else:
                    attr(args)
            else:
                attr()
        except:
            self.disconnect()

        return ''

    def is_connected(self):
        self.connected = False if self.cast is None else self.cast.socket_client.is_connected

        return super(Chromecast, self).is_connected()

    def connect(self):
        self.connected = False

        if self.cast is None:
            Chromecast.discoverDevices(self.logger)

            device_name = self.config['name']
            self.cast = Chromecast.CAST_LIST.get(device_name)

            if not self.cast:
                self.logger.debug(f'Device not found: {device_name}')
                return

        self.cast.wait()
        self.connected = self.cast.socket_client.is_connected
        if not self.connected:
            self.disconnect()

    def disconnect(self):
        try:
            self.cast.disconnect()
        except:
            pass
        self.cast = None
        Chromecast.CAST_LIST[self.config['name']] = None

    @ staticmethod
    def processParams(config, param):
        config_changed = False
        config.setdefault('values', {})

        playlists = param.get(Chromecast.PLAYLISTS_KEY_NAME)
        if playlists is not None:
            values = []
            for playlist in playlists:
                values.append({
                    'value': playlist['name'],
                    'param': [playlist['url'], playlist['type']]
                })
            if config['values'].get(Chromecast.PLAYLISTS_KEY_NAME) != values:
                config['values'][Chromecast.PLAYLISTS_KEY_NAME] = values
                config_changed = True

        apps = param.get(Chromecast.APPS_KEY_NAME)
        if apps is not None:
            values = list(config.get('coreApps', []))

            for app in apps:
                values.append({
                    'value': app['name'],
                    'param': app['app_id']
                })

            defaultApp = config.get('defaultApp')
            if defaultApp:
                values.append(defaultApp)

            if config['values'].get(Chromecast.APPS_KEY_NAME) != values:
                config['values'][Chromecast.APPS_KEY_NAME] = values
                config_changed = True

        enabled = param.get(Chromecast.ENABLED_KEY_NAME)
        if enabled is not None:
            Chromecast.enabled = enabled

        return config_changed

    @ staticmethod
    def discoverDevices(logger):
        if not Chromecast.enabled:
            logger.debug(f'Chromecast disabled')
            return

        if len(Chromecast.CAST_LIST) == 0:
            zeroconf_instance = Zeroconf(unicast=True)
            services, browser = pychromecast.discovery.discover_chromecasts(
                timeout=Chromecast.CAST_CONNECT_TRIES, zeroconf_instance=zeroconf_instance)
            stop_discovery(browser)

            for cast_info in services:
                cast = pychromecast.get_chromecast_cast_info(
                    cast_info, zeroconf_instance)
                friendly_name = cast.device.friendly_name
                logger.debug(f'Found Chromecast device {friendly_name}')
                Chromecast.CAST_LIST[friendly_name] = cast

        result = {}
        for name in Chromecast.CAST_LIST.keys():
            result[utils.desc_to_name(name)] = {
                'name': name,
                'driver': 'chromecast'
            }

        return result
