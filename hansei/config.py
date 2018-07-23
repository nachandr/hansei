# coding=utf-8
"""Tools for managing information about test systems.

Hansei needs to know what servers it can talk to and how to access those
systems. For example, it needs to know the username, hostname and password of a
system in order to SSH into it.
"""
import os
from copy import deepcopy

from xdg import BaseDirectory

import yaml

from hansei import exceptions


# `get_config` uses this as a cache. It is intentionally a global. This design
# lets us do interesting things like flush the cache at run time or completely
# avoid a config file by fetching values from the UI.
_CONFIG = None


def get_config():
    """Return a copy of the global config dictionary.

    This method makes use of a cache. If the cache is empty, the configuration
    file is parsed and the cache is populated. Otherwise, a copy of the cached
    configuration object is returned.

    :returns: A copy of the global server configuration object.
    """
    global _CONFIG  # pylint:disable=global-statement
    if _CONFIG is None:
        # If config.yaml is present in the directory override the XDG yaml
        repo_config = os.path.realpath('{}/../config.yaml'.format(os.path.basename(__file__)))
        if os.path.exists(repo_config):
            config_yaml  = repo_config
        else:
            config_yaml = _get_config_file_path('hansei', 'config.yaml')

        with open(config_yaml) as f:
            _CONFIG = yaml.load(f)

    env_hostname = os.environ.get('KOKU_HOSTNAME')
    env_port = os.environ.get('KOKU_PORT')
    env_service_admin_user = os.environ.get('KOKU_SERVICE_ADMIN_USER')
    env_service_admin_password = os.environ.get('KOKU_SERVICE_ADMIN_PASSWORD')

    if env_hostname:
        if 'koku' not in _CONFIG:
            _CONFIG['koku'] = {}
        _CONFIG['koku']['hostname'] = env_hostname
    if env_port:
        if 'koku' not in _CONFIG:
            _CONFIG['koku'] = {}
        _CONFIG['koku']['port'] = env_port
    if env_service_admin_user:
        if 'koku' not in _CONFIG:
            _CONFIG['koku'] = {}
        _CONFIG['koku']['username'] = env_service_admin_user
    if env_service_admin_password:
        if 'koku' not in _CONFIG:
            _CONFIG['koku'] = {}
        _CONFIG['koku']['password'] = env_service_admin_password

    return deepcopy(_CONFIG)


def _get_config_file_path(xdg_config_dir, xdg_config_file):
    """Search ``XDG_CONFIG_DIRS`` for a config file and return the first found.

    Search each of the standard XDG configuration directories for a
    configuration file. Return as soon as a configuration file is found. Beware
    that by the time client code attempts to open the file, it may be gone or
    otherwise inaccessible.

    :param xdg_config_dir: A string. The name of the directory that is suffixed
        to the end of each of the ``XDG_CONFIG_DIRS`` paths.
    :param xdg_config_file: A string. The name of the configuration file that
        is being searched for.
    :returns: A string. A path to a configuration file.
    :raises hansei.exceptions.ConfigFileNotFoundError: If the requested
        configuration file cannot be found.
    """
    path = BaseDirectory.load_first_config(xdg_config_dir, xdg_config_file)
    if path and os.path.isfile(path):
        return path
    raise exceptions.ConfigFileNotFoundError(
        'Hansei is unable to find a configuration file. The following '
        '(XDG compliant) paths have been searched: ' + ', '.join([
            os.path.join(config_dir, xdg_config_dir, xdg_config_file)
            for config_dir in BaseDirectory.xdg_config_dirs
        ])
    )
