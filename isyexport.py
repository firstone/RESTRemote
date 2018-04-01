import click
import errno
import os
import shutil
import yaml
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ISY_CONF_FOLDER = 'CONF'
ISY_NET_FOLDER = 'NET'
DEFAULT_TIMEOUT = 4000
DEFAULT_METHOD = 'PUT'
STATE_VAR_MESSAGE = '/${var.2.<replace with stare resource ID>}'

REQUEST = '''{} /{} HTTP/1.1\r
Host: {}:{}\r
User-Agent: Mozilla/4.0\r
Connection: Close\r
Content-Type: application/x-www-form-urlencoded\r
Content-Length: 0\r
\r
'''

curResourceID = 0


@click.command()
@click.option('-c', '--config', help='Config file', type=click.File('r'),
    required=True)
@click.option('-d', '--destination', help='Config file',
    type=click.Path(writable=True), required=True)
@click.option('-o', '--output', help='Output file name', required=True)
@click.option('-i', '--input', help='Input file (existing network resources backup)',
    type=click.File('r'))
@click.option('-h', '--host', help='Host running RESTRemote', required=True)
@click.option('-t', '--temp', help='Do not remote temp files', is_flag=True)
def ISYExport(config, destination, output, input, host, temp):
    configData = yaml.load(config)
    configData['host'] = host

    if input:
        print "Extracting existing resources from", input.name
        with ZipFile(input) as inputFile:
            inputFile.extractall(destination)

    global curResourceID
    resources = {}
    commands = {}
    maxResourceID = 0
    outputFileName = os.path.join(destination, ISY_CONF_FOLDER, ISY_NET_FOLDER,
        'RES.CFG')
    try:
        with open(outputFileName, 'r') as resourceFile:
            resourceTree = ET.parse(resourceFile).getroot()
            for resource in resourceTree:
                curResourceID = 0
                for id in resource.iter('id'):
                    curResourceID = int(id.text)
                    if maxResourceID < curResourceID:
                        maxResourceID = curResourceID
                for name in resource.iter('name'):
                    resources[name.text] = resource
    except:
        resourceTree = ET.Element('NetConfig')

    print 'Found', maxResourceID, 'existing resources'
    curResourceID = maxResourceID + 1

    print "Exporting ISY network resources from", config.name, "to", destination

    for driverName, driverData in configData['drivers'].iteritems():
        for commandName, commandData in driverData['commands'].iteritems():
            if not commandData.get('result'):
                simpleCommand = True
                resourceName = driverName + '.' + commandName
                command = driverName + '/' + commandName
                if commandData.get('acceptsNumber'):
                    print 'Create state variable for', resourceName
                    resourceID = addResource(configData, resources, resourceTree,
                        resourceName)
                    commands[resourceID] = command + STATE_VAR_MESSAGE
                    simpleCommand = False

                if 'values' in commandData:
                    for value in commandData['values']:
                        resourceID = addResource(configData, resources,
                            resourceTree, resourceName + '/' + value)
                        commands[resourceID] = command + '/' + value
                    simpleCommand = False

                if simpleCommand:
                    resourceID = addResource(configData, resources, resourceTree,
                        resourceName)
                    commands[resourceID] = command

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
            output.write(ET.tostring(resourceTree))

        # Add main resources file to zip
        outputFile.write(outputFileName,
            os.path.relpath(outputFileName, destination))

        # Add RES files to zip
        for resourceID in range(1, curResourceID):
            command = commands.get(resourceID)
            outputFileName = os.path.join(destination, ISY_CONF_FOLDER,
                ISY_NET_FOLDER, str(resourceID) + '.RES')
            if command:
                with open(outputFileName, 'w') as output:
                    output.write(REQUEST.format(DEFAULT_METHOD, command,
                        configData['host'], configData['port']))

            outputFile.write(outputFileName,
                os.path.relpath(outputFileName, destination))

    if not temp:
        shutil.rmtree(os.path.join(destination, ISY_CONF_FOLDER))


def addResource(configData, resources, parent, resourceName):
    resource = resources.get(resourceName)
    if resource is None:
        resource = addNewResource(parent, resourceName)

    updateResource(resource, configData['host'], configData['port'],
        DEFAULT_METHOD)

    for id in resource.iter('id'):
        return int(id.text)

    return -1


def addNewResource(parent, resourceName):
    global curResourceID

    print 'Adding new resource', resourceName
    netRule = ET.SubElement(parent, 'NetRule')
    addElement(netRule, 'name', resourceName)
    addElement(netRule, 'id', str(curResourceID))
    addElement(netRule, 'isModified', 'false')

    controlInfo = ET.SubElement(netRule, 'ControlInfo')
    addElement(controlInfo, 'mode', 'C Escaped')
    addElement(controlInfo, 'protocol', 'http')
    addElement(controlInfo, 'timeout', str(DEFAULT_TIMEOUT))
    ET.SubElement(controlInfo, 'host')
    ET.SubElement(controlInfo, 'port')
    ET.SubElement(controlInfo, 'method')
    addElement(controlInfo, 'encodeURLs', 'false')
    addElement(controlInfo, 'useSNI', 'false')

    curResourceID += 1
    return netRule


def updateResource(resource, host, port, method):
    for element in resource.find('ControlInfo'):
        if element.tag == 'host':
            element.text = host
        elif element.tag == 'port':
            element.text = str(port)
        elif element.tag == 'method':
            element.text = method


def addElement(parent, name, value):
    element = ET.SubElement(parent, name)
    element.text = value

if __name__ == '__main__':
    ISYExport()
