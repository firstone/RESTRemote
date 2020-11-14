#!/usr/bin/env python3
from poly.remotecontroller import RemoteController
import polyinterface
import click
import sys
import yaml


@click.command()
@click.option('-sc', '--serverConfig', help='Server config file', type=click.File('r'), required=True)
@click.option('-c', '--config', help='Config file', type=click.File('r'), required=False)
def PolyRemote(serverconfig, config):
    configData = yaml.safe_load(serverconfig)
    if config:
        configData.update(yaml.safe_load(config))

    try:
        polyglot = polyinterface.Interface(configData['controller']['name'])
        polyglot.start()
        controller = RemoteController(polyglot, configData, config is not None)
        controller.name = configData['controller']['name']
        controller.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)


if __name__ == '__main__':
    PolyRemote()
