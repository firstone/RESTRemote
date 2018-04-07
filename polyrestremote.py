#!/usr/bin/env python3
from poly.remotecontroller import RemoteController
import polyinterface
import click
import sys
import yaml


@click.command()
@click.option('-c', '--config', help='Config file', type=click.File('r'),
    required=True)
def PolyRemote(config):
    configData = yaml.load(config)
    try:
        polyglot = polyinterface.Interface(configData['controller']['name'])
        polyglot.start()
        controller = RemoteController(polyglot, configData)
        controller.name = configData['controller']['name']
        controller.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

if __name__ == '__main__':
    PolyRemote()
