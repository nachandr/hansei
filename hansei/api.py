# coding=utf-8
"""Client for working with KOKU's API.

This module provides a flexible API client for talking with the koku
server, allowing the user to customize how return codes are handled depending
on the context.

"""
from json import JSONDecodeError
from pprint import pformat
from urllib.parse import urljoin, urlunparse

import requests
from requests.exceptions import HTTPError

from hansei import config
from hansei import exceptions
from hansei.constants import (
    KOKU_API_VERSION,
    KOKU_TOKEN_PATH,
    KOKU_DEFAULT_USER,
    KOKU_DEFAULT_PASSWORD,
)


def raise_error_for_status(response):
    """Generate an error message and raise HTTPError for bad return codes.

    :raises: ``requests.exceptions.HTTPError`` if the response status code is
        in the 4XX or 5XX range.
    """
    r = response
    if (r.status_code >= 400) and (r.status_code <= 599):
        error_msgs = (
            '\n============================================================\n'
            '\nThe request you made received a status code that indicates\n'
            'an error was encountered. Details about the request and the\n'
            'response are below.\n'
            '\n============================================================\n'
        )

        try:
            response_message = 'json_error_message : {}'.format(
                pformat(r.json()))
        except JSONDecodeError:
            response_message = 'text_error_message : {}'.format(
                pformat(r.text))

        error_msgs += '\n\n'.join(
            [
                'request path : {}'.format(pformat(
                    r.request.path_url)),
                'request body : {}'.format(pformat(
                    r.request.body)),
                'request headers : {}'.format(pformat(
                    r.request.headers)),
                'response code : {}'.format(r.status_code),
                '{error_message}'.format(error_message=response_message)
            ]
        )
        error_msgs += (
            '\n============================================================\n'
        )
        raise HTTPError(error_msgs)


def echo_handler(response):
    """Immediately return ``response``."""
    return response


def code_handler(response):
    """Check the response status code, and return the response.

    :raises: ``requests.exceptions.HTTPError`` if the response status code is
        in the 4XX or 5XX range.
    """
    raise_error_for_status(response)
    return response


def json_handler(response):
    """Like ``code_handler``, but also return a JSON-decoded response body.

    Do what :func:`hansei.api.code_handler` does. In addition, decode the
    response body as JSON and return the result.
    """
    raise_error_for_status(response)
    return response.json()


class Client(object):
    """A client for interacting with the koku API.

    This class is a wrapper around the ``requests.api`` module provided by
    `Requests`_. Each of the functions from that module are exposed as methods
    here, and each of the arguments accepted by Requests' functions are also
    accepted by these methods. The difference between this class and the
    `Requests`_ functions lies in its configurable request and response
    handling mechanisms.

    All requests made via this client use the base URL of the Koku server
    provided in your ``$XDG_CONFIG_HOME/hansei/config.yaml``.

    You can override this base url by assigning a new value to the url
    field.

    Example::
        >>> from hansei import api
        >>> client = api.Client()
        >>> # I can now make requests to the KOKU server
        >>> # using relative paths, because the base url is
        >>> # was set using my config file.
        >>>
        >>> client.get('customers/users/')
        >>>
        >>> # now if I want to do something else,
        >>> # I can change the base url
        >>> client.url = 'https://www.whatever.com'

    .. _Requests: http://docs.python-requests.org/en/master/
    """

    def __init__(
            self, response_handler=None, url=None,
            authenticate=True, username=None, password=None):
        """Initialize this object, collecting base URL from config file.

        If no response handler is specified, use the `code_handler` which will
        raise an exception for 'bad' return codes.


        If no URL is specified, then the config file will be parsed and the URL
        will be built by reading the hostname, port and https values. You can
        configure the default URL by including the following on your hansei
        configuration file::

            koku:
                hostname: <machine_hostname_or_ip_address>
                port: <port>  # if not defined will take the default port
                              # depending on the https config: 80 if https is
                              # false and 443 if https is true.
                https: false  # change to true if server is published over
                              # https. Defaults to false if not defined

        Arguments: 
            response_handler - Customer handler wrapper for formatting response
            url - Url for the Koku server. Default is localhost (127.0.0.1)
            authenticate - If True, login to the server during initialization
            username - Username used for server authentication
            password - Password used for server authentication
        """
        # Stores the response of the last request made.
        self._last_response = None
        self.url = url
        self.token = None
        cfg = config.get_config().get('koku', {})
        self.verify = cfg.get('ssl-verify', False)

        if not self.url:
            hostname = cfg.get('hostname')

            if not hostname:
                raise exceptions.KokuBaseUrlNotFound(
                    "\n'koku' section specified in hansei config file, but"
                    "no 'hostname' key found."
                )

            scheme = 'https' if cfg.get('https', False) else 'http'
            port = str(cfg.get('port', ''))
            netloc = hostname + ':{}'.format(port) if port else hostname
            self.url = urlunparse(
                (scheme, netloc, KOKU_API_VERSION, '', '', ''))

        if not self.url:
            raise exceptions.KOKUBaseUrlNotFound(
                'No base url was specified to the client either with the '
                'url="host" option or with the hansei config file.')

        if response_handler is None:
            self.response_handler = code_handler
        else:
            self.response_handler = response_handler

        if authenticate:
            self.login(username=username, password=password)

    @property
    def logged_in(self):
        """Returns True if the client is currently logged in"""
        return self.token is not None

    def login(self, username, password):
        """Login to the server to receive an authorization token.

        Arguments:
            username - Username for initial server authentication
            password - Password for initial server authentication
        """
        login_request = self.request(
            'POST',
            urljoin(self.url, KOKU_TOKEN_PATH),
            json={
                'username': username,
                'password': password
            }
        )
        self.token = login_request.json()['token']
        return login_request

    def logout(self, **kwargs):
        """Start sending unauthorized requests.

        Send a PUT request /api/v1/users/logout to make
        current token invalid.
        """
        self.token = None

    def get_user(self, **kwargs):
        """Get the username of the user logged in.

        Send a GET request ot /api/v1/users/current/' and return the response.
        """
        url = urljoin(self.url, 'users/current/')
        return self.request('GET', url, **kwargs)

    def server_status(self, **kwargs):
        """Get the Koku server status

        Send a GET request to /api/v1/status
        """
        url = urljoin(self.url, 'status/')
        return self.request('GET', url, **kwargs)

    def default_headers(self):
        """Build the headers for our request to the server."""
        if self.token:
            return {'Authorization': 'Token {}'.format(self.token)}
        return {}

    def delete(self, endpoint, **kwargs):
        """Send an HTTP DELETE request.
        Arguments:
            endpoint - API endpoint to send request
        """
        url = urljoin(self.url, endpoint)
        return self.request('DELETE', url, **kwargs)

    def get(self, endpoint, **kwargs):
        """Send an HTTP GET request.

        Arguments:
            endpoint - API endpoint to send request
        """
        url = urljoin(self.url, endpoint)
        return self.request('GET', url, **kwargs)

    def options(self, endpoint, **kwargs):
        """Send an HTTP OPTIONS request.

        Arguments:
            endpoint - API endpoint to send request
        """
        url = urljoin(self.url, endpoint)
        return self.request('OPTIONS', url, **kwargs)

    def head(self, endpoint, **kwargs):
        """Send an HTTP HEAD request.

        Arguments:
            endpoint - API endpoint to send request
        """
        url = urljoin(self.url, endpoint)
        return self.request('HEAD', url, **kwargs)

    def post(self, endpoint, payload, **kwargs):
        """Send an HTTP POST request.
        Arguments:
            endpoint - API endpoint to send request
            payload - json data to include in the request
        """
        url = urljoin(self.url, endpoint)
        return self.request('POST', url, json=payload, **kwargs)

    def put(self, endpoint, payload, **kwargs):
        """Send an HTTP PUT request.

        Arguments:
            endpoint - API endpoint to send request
            payload - json data to include in the request
        """
        url = urljoin(self.url, endpoint)
        return self.request('PUT', url, json=payload, **kwargs)

    def request(self, method, url, **kwargs):
        """Send an HTTP request.

        Arguments passed directly in to this method override (but do not
        overwrite!) arguments specified in ``self.request_kwargs``.
        """
        # The `self.request_kwargs` dict should *always* have a "url" argument.
        # This is enforced by `self.__init__`. This allows us to call the
        # `requests.request` function and satisfy its signature:
        #
        #     request(method, url, **kwargs)
        #
        headers = self.default_headers()
        headers.update(kwargs.get('headers', {}))
        kwargs['headers'] = headers
        kwargs.setdefault('verify', self.verify)
        self._last_response = requests.request(method, url, **kwargs)
        return self.response_handler(self._last_response)

    @property
    def last_response(self):
        return self._last_response
