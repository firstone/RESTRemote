#!/usr/bin/env python3
import click
import hashlib
import json
import os
import utils
import xml.etree.ElementTree as ET
import yaml

from drivers.param_parser import ParamParser


@click.command()
@click.option('-c', '--config', help='Config file', type=click.File('r'),
    required=True)
@click.option('-d', '--destination', help='Polyglot profile destination directory',
    type=click.Path(writable=True), required=True)
@click.option('-s', '--serverInfo', help='Generate server info', default=False,
    is_flag=True)
def PolyRemote(config, destination, serverinfo):
    print("Generating Polyglot profile")

    factory = ProfileFactory(destination, yaml.load(config))
    factory.create()
    factory.write()
    if serverinfo:
        factory.write_server_info(config.name)


class ProfileFactory(object):

    NODE_NAME = 'ND-{}-NAME = {}'
    NODE_ICON = 'ND-{}-ICON = {}'
    COMMAND_NAME = 'CMD-{}-NAME = {}'
    STATUS_NAME = 'ST-{}-{}-NAME = {}'
    PROFILE_DIR = 'profile'
    EDITOR_FILE = [ 'editor', 'editors.xml' ]
    NLS_FILE = [ 'nls', 'en_us.txt' ]
    NODES_FILE = [ 'nodedef', 'nodedefs.xml' ]

    def __init__(self, destination, config):
        self.destination = destination
        self.config = config

        self.nodeTree = ET.Element('nodeDefs')
        self.editorTree = ET.Element('editors')

        self.nlsData = []

    def create(self):
        # Write controller labels
        self.nlsData.append('# controller labels')
        self.nlsData.append('')
        self.nlsData.append(self.NODE_NAME.format('controller',
            self.config['controller']['name'] + ' Controller'))
        self.nlsData.append(self.NODE_ICON.format('controller',
            self.config['controller'].get('icon', 'GenericCtl')))
        self.nlsData.append('')
        self.nlsData.append(self.COMMAND_NAME.format('ctl-DISCOVER',
            'Re-Discover'))
        self.nlsData.append(self.STATUS_NAME.format('ctl', 'ST',
            self.config['controller']['name'] + ' Online'))
        self.nlsData.append('')

        # Write controller node
        nodeDef = ET.SubElement(self.nodeTree, 'nodeDef', id='controller',
            nls='ctl')
        sts = ET.SubElement(nodeDef, 'sts')
        ET.SubElement(sts, 'st', id='ST', editor='bool')
        cmds = ET.SubElement(nodeDef, 'cmds')
        ET.SubElement(cmds, 'sends')
        accepts = ET.SubElement(cmds, 'accepts')
        ET.SubElement(accepts, 'cmd', id='DISCOVER')

        editor = ET.SubElement(self.editorTree, 'editor', id='bool')
        ET.SubElement(editor, 'range', uom='2', subset='0,1')

        # Write primary devices
        for driverName, driverData in self.config['drivers'].items():
            polyCommandsData = self.config['poly']['drivers'].get(driverName, {}).get('commands', {})
            paramParser = ParamParser(driverData, True)
            nodeDesc = driverData.get('description', utils.name_to_desc(driverName))
            nlsName = utils.name_to_nls(driverName)
            nlsData = [ self.STATUS_NAME.format(nlsName, 'ST', nodeDesc + ' Online') ]
            states = self.write_node_info(polyCommandsData, paramParser,
                driverName, nodeDesc, nlsName, driverData,
                nlsData)
            ET.SubElement(states, 'st', id='ST', editor='bool')
            # Write sub devices
            for groupName, groupData in driverData.get('commandGroups', {}).items():
                polyGroupData = self.config['poly']['commandGroups'].get(groupName)
                if polyGroupData:
                    self.write_node_info(polyCommandsData, paramParser,
                        driverName + '_' + groupName,
                        nodeDesc + ' ' + utils.name_to_desc(groupName),
                        utils.name_to_nls(
                            driverName + polyGroupData.get('nls', groupName)),
                        groupData)

    def write(self):
        has_changed = False

        nlsFile = os.path.join(self.destination, self.PROFILE_DIR, *self.NLS_FILE)
        utils.create_dir(nlsFile)

        hash = self.get_hash(nlsFile)

        with open(nlsFile, 'w') as output:
            for line in self.nlsData:
                output.write(line)
                output.write('\n')

        if hash != self.get_hash(nlsFile):
            has_changed = True

        nodesFile = os.path.join(self.destination, self.PROFILE_DIR,
            *self.NODES_FILE)
        utils.create_dir(nodesFile)

        hash = self.get_hash(nodesFile)

        with open(nodesFile, 'w') as output:
            output.write(ET.tostring(self.nodeTree).decode())

        if hash != self.get_hash(nodesFile):
            has_changed = True

        editorFile = os.path.join(self.destination, self.PROFILE_DIR,
            *self.EDITOR_FILE)
        utils.create_dir(editorFile)

        hash = self.get_hash(editorFile)

        with open(editorFile, 'w') as output:
            output.write(ET.tostring(self.editorTree).decode())

        if hash != self.get_hash(editorFile):
            has_changed = True

        return has_changed

    def write_server_info(self, config_file_name):
        with open('version.txt', 'r') as versionFile:
            version = versionFile.read().strip()

        with open(os.path.join(self.destination, self.PROFILE_DIR, 'version.txt'),
            'w') as versionFile:
            versionFile.write(version)
            versionFile.write('\n')

        with open('server.yaml', 'r') as serverInfo:
            serverData = yaml.load(serverInfo)
        serverData['executable'] += ' --serverConfig ' + config_file_name
        serverData['credits'][0]['version'] = version

        description = ''
        for driverData in self.config['drivers'].values():
            description += ', ' + driverData['description']
            if driverData.get('experimental', False):
                description += ' (exp)'

        serverData['description'] += ' Supported: ' + description[2:]
        with open('server.json', 'w') as serverInfo:
            serverInfo.write(json.dumps(serverData, indent=4))

    def write_node_info(self, polyCommandsData, paramParser, nodeName, nodeDesc,
        nlsName, nodeData, nlsData=[]):
        assert len(nlsName) <= 16, 'Node NLS name is too long: {}'.format(nlsName)

        self.nlsData.append('# ' + nodeName + ' labels\n')
        self.nlsData.append(self.NODE_NAME.format(nodeName, nodeDesc))
        self.nlsData.append(self.NODE_ICON.format(nodeName,
            nodeData.get('icon', 'GenericCtl')))
        self.nlsData.extend(nlsData)
        nodeDef = ET.SubElement(self.nodeTree, 'nodeDef', id=nodeName, nls=nlsName)
        states = ET.SubElement(nodeDef, 'sts')
        cmds = ET.SubElement(nodeDef, 'cmds')
        ET.SubElement(cmds, 'sends')
        accepts = ET.SubElement(cmds, 'accepts')
        for commandName, commandData in nodeData['commands'].items():
            commandKey = nodeName + '_' + commandName
            nlsCommand = utils.name_to_nls(commandKey)
            polyData = polyCommandsData.get(commandName, {})
            polyDriverName = polyData.get('driver', {}).get('name')
            if not commandData.get('result'):
                self.nlsData.append(self.COMMAND_NAME.format(
                    nlsName + '-' + commandName,
                    commandData.get('description', utils.name_to_desc(commandName))))
                cmd = ET.SubElement(accepts, 'cmd', id=commandName)
                param = None
                if (commandData.get('acceptsNumber') or
                    commandData.get('acceptsHex') or
                    commandData.get('acceptsFloat')):
                    param = ET.SubElement(cmd, 'p', id='', editor=nlsCommand)
                    editor = ET.SubElement(self.editorTree, 'editor', id=nlsCommand)
                    range = ET.SubElement(editor, 'range')
                    for rangeKey, rangeValue in polyData['param'].items():
                        range.set(rangeKey, str(rangeValue))
                elif 'value_set' in commandData:
                    param = ET.SubElement(cmd, 'p', id='', editor=nlsCommand)
                    self.add_driver_desc(nlsCommand,
                        paramParser.value_sets[commandData['value_set'] + '_names'])

                if polyDriverName:
                    if param is None:
                        raise RuntimeError('Driver configured but command is not configured for parameters: ' + commandName)
                    param.set('init', polyDriverName)

            elif commandData.get('readOnly', False) and 'value_set' in commandData:
                self.add_driver_desc(nlsCommand,
                    paramParser.value_sets[commandData['value_set'].replace('_reverse', '') + '_names'])

            if polyDriverName:
                ET.SubElement(states, 'st', id=polyDriverName,
                    editor=nlsCommand)

                self.nlsData.append(self.STATUS_NAME.format(nlsName,
                    polyDriverName,
                    polyData['driver'].get('description',
                        utils.name_to_desc(commandName))))

        self.nlsData.append('')
        return states

    def add_driver_desc(self, nlsCommand, names):
        editor = ET.SubElement(self.editorTree, 'editor', id=nlsCommand)
        maxIndex = len(names) - 1 if len(names) else 0
        ET.SubElement(editor, 'range', uom='25',
            subset='0-' + str(maxIndex), nls=nlsCommand + '_I')
        for key, value in names.items():
            self.nlsData.append(nlsCommand + '_I-' + str(key) +
                ' = ' + value)

    def get_hash(self, file_name):
        if not os.path.isfile(file_name):
            return ''

        hash = hashlib.sha256()
        with open(file_name, 'rb') as file:
            hash.update(file.read())

        return hash.hexdigest()

if __name__ == '__main__':
    PolyRemote()
