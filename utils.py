import copy
import errno
import os


def flatten_commands(config):
    config.setdefault('commands', {})
    commands = config['commands']
    for commandGroup in config.get('commandGroups', {}).values():
        commands.update(commandGroup['commands'])


def merge_commands(config):
    result = copy.deepcopy(config)
    flatten_commands(result)

    return result


def name_to_desc(name):
    labels = name.split('_')
    return ' '.join([label.capitalize() for label in labels])


def name_to_nls(name):
    nls = ''.join(name.split('_')).upper()

    return nls


def create_dir(fileName):
    if not os.path.exists(os.path.dirname(fileName)):
        try:
            os.makedirs(os.path.dirname(fileName))
        except OSError as error:
            if error.errno != errno.EEXIST:
                raise
