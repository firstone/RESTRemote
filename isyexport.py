import click
import errno
import os
import shutil
import yaml
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ISY_CONF_FOLDER = 'CONF'
ISY_NET_FOLDER = 'NET'

REQUEST = '''{} /{} HTTP/1.1\r
Host: {}:{}\r
User-Agent: Mozilla/4.0\r
Connection: Close\r
Content-Type: application/x-www-form-urlencoded\r
Content-Length: 0\r
\r
'''


@click.command()
@click.option('-c', '--config', help='Config file', type=click.File('r'), required=True)
@click.option('-d', '--destination', help='Config file', type=click.Path(writable=True), required=True)
@click.option('-o', '--output', help='Output file name', required=True)
@click.option('-t', '--temp', help='Do not remote temp files', is_flag=True)
def ISYExport(config, destination, output, temp):
    print "Exporting ISY network resources from", config.name, "to", destination
    configData = yaml.load(config)
    netConfig = ET.Element('NetConfig')
    currentID = 0
    commands = {}
    for driverName, driverData in configData['drivers'].iteritems():
        for commandName, commandData in driverData['commands'].iteritems():
            if not commandData.get('result'):
                currentID += 1
                simpleCommand = True
                resourceName = driverName + '.' + commandName
                if commandData.get('acceptsNumber'):
                    print 'Create state variable', resourceName
                    addResource(configData, netConfig, currentID, resourceName)
                    commands[currentID] = resourceName + '/$' + resourceName
                    simpleCommand = False

                if 'values' in commandData:
                    for value in commandData['values']:
                        addResource(configData, netConfig, currentID,
                            resourceName + '/' + value)
                        commands[currentID] = resourceName + '/' + value
                    simpleCommand = False

                if simpleCommand:
                    addResource(configData, netConfig, currentID, resourceName)
                    commands[currentID] = resourceName

    outputFileName = os.path.join(destination, ISY_CONF_FOLDER, ISY_NET_FOLDER,
        'RES.CFG')
    if not os.path.exists(os.path.dirname(outputFileName)):
        try:
            os.makedirs(os.path.dirname(outputFileName))
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise

    with ZipFile(os.path.join(destination, output), 'w') as outputFile:

        with open(outputFileName, 'w') as output:
            output.write(ET.tostring(netConfig))

        outputFile.write(outputFileName)

        for commandID, command in commands.iteritems():
            outputFileName = os.path.join(destination, ISY_CONF_FOLDER,
                ISY_NET_FOLDER, str(commandID) + '.RES')
            with open(outputFileName, 'w') as output:
                output.write(REQUEST.format('PUT', command, configData['host'],
                    configData['port']))

            outputFile.write(outputFileName)

    if not temp:
        shutil.rmtree(os.path.join(destination, ISY_CONF_FOLDER))


def addResource(configData, netConfig, currentID, resourceName):
    netRule = ET.SubElement(netConfig, 'NetRule')
    addElement(netRule, 'name', resourceName)
    addElement(netRule, 'id', str(currentID))
    addElement(netRule, 'isModified', 'false')

    controlInfo = ET.SubElement(netRule, 'ControlInfo')
    addElement(controlInfo, 'mode', 'C Escaped')
    addElement(controlInfo, 'protocol', 'http')
    addElement(controlInfo, 'host', configData['host'])
    addElement(controlInfo, 'port', str(configData['port']))
    addElement(controlInfo, 'timeout', '4000')
    addElement(controlInfo, 'method', 'PUT')
    addElement(controlInfo, 'encodeURLs', 'false')
    addElement(controlInfo, 'useSNI', 'false')


def addElement(parent, name, value):
    element = ET.SubElement(parent, name)
    element.text = value

if __name__ == '__main__':
    ISYExport()
