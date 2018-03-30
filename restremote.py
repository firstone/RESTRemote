import click
from flask import abort
from flask import Flask
import json
import sys
import yaml

app = Flask(__name__)
modules = {}


@app.route('/<string:moduleName>/<string:commandName>', methods=['PUT'])
@app.route('/<string:moduleName>/<string:commandName>/<string:args>', methods=['PUT'])
def executeCommand(moduleName, commandName, args=None):
    try:
        return json.dumps(getattr(modules[moduleName], 'executeCommand')(
            commandName, args))
    except Exception as e:
        sys.stderr.write('Exception: ' + str(e) + '\n')
        abort(400)


@app.route('/<string:moduleName>/<string:commandName>', methods=['GET'])
@app.route('/<string:moduleName>/<string:commandName>/<string:args>', methods=['GET'])
def getData(moduleName, commandName, args=None):
    try:
        return json.dumps(getattr(modules[moduleName], 'getData')(
            commandName, args))
    except Exception as e:
        sys.stderr.write('Exception: ' + str(e) + '\n')
        abort(400)


@app.route('/drivers', methods=['GET'])
def getDriverList():
    try:
        return json.dumps({
            'drivers': modules.keys()
        })
    except Exception as e:
        sys.stderr.write('Exception: ' + str(e) + '\n')
        abort(400)


@click.command()
@click.option('-c', '--config', help='Config file', type=click.File('r'), required=True)
@click.option('-d', '--debug', help='Run server in debug mode', default=False, is_flag=True)
def RESTRemote(config, debug):
    print "Starting with config file", config.name
    configData = yaml.load(config)
    sys.path.append(configData['driversPath'])
    for driverName, driverData in configData['drivers'].iteritems():
        if driverData.get('enable', True):
            print "Loading driver", driverName
            module = __import__(driverName)
            modules[driverName] = getattr(module, driverData['name'])(driverData)
    print "debug", debug
    app.run(host=configData.get('host', 'localhost'), port=configData.get('port', 5000),
        debug=debug)


if __name__ == '__main__':
    RESTRemote()
