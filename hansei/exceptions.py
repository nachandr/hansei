# coding=utf-8
"""Custom exceptions defined by Hansei."""


class KokuException(Exception):
    """Base exception thrown during Hansei execution

    Use this to differentiate between generic exception and exceptions we throw"""


class ConfigFileNotFoundError(KokuException):
    """We cannot find the requested Hansei configuration file.

    See :mod:`hansei.config` for more information on how configuration files
    are handled.
    """


class KokuBaseUrlNotFound(KokuException):
    """Was not able to build a base URL with the config file information.

    Check the expected configuration file format on the API Client
    documentation.
    """


