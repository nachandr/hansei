# coding=utf-8
"""Custom exceptions defined by Camayoc."""


class KokuException(Exception):
    """Base exception thrown during Koku-QE execution

    Use this to differentiate between generic exception and exceptions we throw"""


class ConfigFileNotFoundError(KokuException):
    """We cannot find the requested Camayoc configuration file.

    See :mod:`kokuqe.config` for more information on how configuration files
    are handled.
    """


class KokuBaseUrlNotFound(KokuException):
    """Was not able to build a base URL with the config file information.

    Check the expected configuration file format on the API Client
    documentation.
    """


