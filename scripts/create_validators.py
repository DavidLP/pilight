''' This script reverse engineers the protocols defined in pilight.

    It converts them to voloptuous schemes to allow protocol validation
    before sending data to the pilight daemon.

    'git' python package has to be installed.

    TODO: use regex for numbers
'''


import re
import glob

import voluptuous as vol
import git

# git.Repo.clone_from(url=r'https://github.com/pilight/pilight',
#                 to_path='pilight')


def parse_option(option_string):
    if 'OPTION_NO_VALUE' in option_string:
        option = re.findall(r'\"(.*?)\"', option_string)[0]
        # The options without values seem to still need a value
        # when used with pilight-daemon, but this are not mandatory
        # options
        # E.G.: option 'on' is 'on': 1
        return {vol.Optional(option): vol.Coerce(int)}
    elif 'OPTION_HAS_VALUE' in option_string:
        options = re.findall(r'\"(.*?)\"', option_string)
        option = options[0]
        regex = None
        if len(options) > 1:  # Option has specified value by regex
            regex = options[1]
        if 'JSON_NUMBER' in option_string:
            return {vol.Required(option): vol.Coerce(int)}
        elif 'JSON_STRING' in option_string:
            return {vol.Required(option): vol.Coerce(str)}
        else:
            raise
    elif 'OPTION_OPT_VALUE' in option_string:
        options = re.findall(r'\"(.*?)\"', option_string)
        option = options[0]
        regex = None
        if len(options) > 1:  # Option has specified value by regex
            regex = options[1]
        if 'JSON_NUMBER' in option_string:
            return {vol.Required(option): vol.Coerce(int)}
        elif 'JSON_STRING' in option_string:
            return {vol.Required(option): vol.Coerce(str)}
        else:
            raise
    else:
        print(option_string)
        raise

    raise


def parse_protocol(file):
    protocol = {}
    with open(file, 'r') as in_file:
        for line in in_file:
            # Omit commented code
            if '//' in line:
                continue
            # Omit GUI specific protocol settings
            if 'GUI_SETTING' in line:
                continue
            # Get protocol id (= name string)
            if 'protocol_set_id' in line:
                p_id = line.partition('\"')[-1].rpartition('\"')[0]
            # Get protocol options (key/value pairs)
            if 'options_add' in line:
                protocol.update(parse_option(line))

    return {p_id: protocol}


def get_protocols(path='pilight/**/433*/*.c'):
    for filename in glob.iglob(path, recursive=True):
        yield filename

if __name__ == '__main__':

    protocols = None
    for protocol in get_protocols():
        if not protocols:
            # , extra=vol.ALLOW_EXTRA)
            protocols = vol.Schema(parse_protocol(protocol),
                                   # Allows additional protcols but
                                   # also additional protcol keys
                                   # HOWTO fix?
                                   extra=vol.ALLOW_EXTRA)
        else:
            protocols.extend(parse_protocol(protocol))
