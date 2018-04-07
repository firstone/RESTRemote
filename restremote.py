#!/usr/bin/env python3
import click
from flask import abort
from flask import Flask
import importlib
import json
import logging
import sys
import utils
import yaml

app = Flask(__name__)
devices = {}
logger = logging.getLogger('RESTRemote')


@app.route('/<string:deviceName>/<string:commandName>', methods=['PUT'])
@app.route('/<string:deviceName>/<string:commandName>/<string:args>', methods=['PUT'])
def execute_command(deviceName, commandName, args=None):
    try:
        return json.dumps(getattr(devices[deviceName], 'executeCommand')(
            commandName, args))
    except Exception as e:
        logger.exception('Exception: %s', e)
        abort(400)


@app.route('/<string:deviceName>/<string:commandName>', methods=['GET'])
@app.route('/<string:deviceName>/<string:commandName>/<string:args>', methods=['GET'])
def get_data(deviceName, commandName, args=None):
    try:
        return json.dumps(getattr(devices[deviceName], 'getData')(
            commandName, args))
    except Exception as e:
        logger.exception('Exception: %s', e)
        abort(400)


@app.route('/devices', methods=['GET'])
def get_device_list():
    try:
        deviceList = []
        for deviceName, device in devices.items():
            deviceList.append({
                'name': deviceName,
                'is_connected': device.is_connected()
            })

        return json.dumps({
            'devices': deviceList
        })
    except Exception as e:
        logger.exception('Exception: %s', e)
        abort(400)


@click.command()
@click.option('-c', '--config', help='Config file', type=click.File('r'), required=True)
@click.option('-d', '--debug', help='Run server in debug mode', default=False, is_flag=True)
def RESTRemote(config, debug):
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s')
    logger.setLevel('DEBUG')
    logger.info('Starting with config file %s', config.name)
    configData = yaml.load(config)
    sys.path.append(configData['driversPath'])
    for deviceName, deviceData in configData['devices'].items():
        if deviceData.get('enable', True):
            driverName = deviceData['driver']
            logger.info('Loading device %s using driver %s', deviceName, driverName)
            driver = importlib.import_module('drivers.' + driverName)
            deviceData.update(configData['drivers'][driverName])
            utils.flatten_commands(deviceData)
            devices[deviceName] = getattr(driver,
                deviceData.get('moduleName', driverName.capitalize()))(
                    deviceData, logger)
            devices[deviceName].start()

    app.run(host=configData.get('bindHost', '0.0.0.0'), port=configData.get('port', 5000),
        debug=debug)


if __name__ == '__main__':
    RESTRemote()
