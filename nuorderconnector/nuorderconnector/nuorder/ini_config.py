import configparser
import os
import os.path as op

PATH = os.environ.get('NUORDER_CONFIG', '~/.config/nuorder.ini')

_config_path = op.expanduser(PATH)
_config = configparser.ConfigParser()

if op.isfile(_config_path):
    _config.read(_config_path)


class ConfigKeyMissing(KeyError):
    """A config key is missing, and no fallback was provided."""


def get(section, key, default=None, required=True):
    try:
        return _config[section][key]
    except KeyError:
        if default is None and required:
            raise ConfigKeyMissing(
                '`{}` missing, and no default provided.'.format(key)
            )
        else:
            return default
