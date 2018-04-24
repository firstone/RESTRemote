class ParamParser(object):
    '''Performs input values to device parameters (and reverse)
    translations. Input value can be string or numeric'''

    REPLACE_CHARS = [
        { 'match': ' ', 'replace': '_' },
        { 'match': '()', 'replace': '' }
    ]

    def __init__(self, config, use_numeric_key=False):
        self.value_sets = {}
        for value_set_key, value_set_data in config.get('values', {}).items():
            self.create_value_sets(self.value_sets, value_set_key,
                value_set_data, use_numeric_key)

        for command_name, command_data in config.get('commands', {}).items():
            self.process_command_values(command_name, command_data,
                use_numeric_key)

        for command_group in config.get('commandGroups', {}).values():
            for command_name, command_data in command_group['commands'].items():
                self.process_command_values(command_name, command_data,
                    use_numeric_key)

    def process_command_values(self, command_name, command_data, use_numeric_key):
        if 'values' in command_data:
            self.create_value_sets(self.value_sets, command_name,
                command_data['values'], use_numeric_key)
            command_data['value_set'] = command_name

    def create_value_sets(self, value_sets, value_set_key, value_set_data,
        use_numeric_key):
        '''Creates forward and reverse lookup maps'''
        value_sets[value_set_key] = forward_set = {}
        value_sets[value_set_key + '_reverse'] = reverse_set = {}
        value_sets[value_set_key + '_names'] = name_set = {}
        for numeric_value, item in enumerate(value_set_data):
            key = str(numeric_value) if use_numeric_key else item['value']
            param = item.get('param', item['value'])
            forward_set[self.url_encode(key)] = param
            reverse_set[param] = key
            name_set[key] = item['value']

    def translate_param(self, command, value, defaultValue=None):
        if value is not None and 'value_set' in command:
            return self.value_sets[command['value_set']].get(value, value)

        return defaultValue if defaultValue is not None else value

    def url_encode(self, value):
        result = ''
        for c in str(value):
            for replace in ParamParser.REPLACE_CHARS:
                if c in replace['match']:
                    c = replace['replace']
            result += c

        return result.lower()
