# coding: utf-8
"""Models for use with the Koku API."""

from pprint import pformat
from urllib.parse import urljoin

from kokuqe import api
from kokuqe.exceptions import KokuException
from kokuqe.constants import (
    KOKU_CUSTOMER_PATH,
    KOKU_USER_PATH,
)

class KokuObject(object):
    """A base class for other KOKU models.

    Child classes should define member variables that match the names and format supplied in a POST
    request used to create this object on the koku server
    """

    def __init__(
            self,
            client=None,
            uuid=None):
        """Provide shared methods for KOKU model objects."""
        # we want to allow for an empty string name
        self.uuid = uuid
        self.client = client if client else api.Client()
        self.endpoint = ''

    def fields(self):
        """Return a dictionary with all fields.

        The fields are all data items that may be returned when a `GET` request
        is sent to the endpoint. It excludes items specific to kokuqe such as
        the client and endpoint associated with objects of this type.
        """
        fields = self.payload()
        fields['uuid'] = self.uuid
        return fields

    def path(self):
        """Return the path to this object on the server.

        This concatenates the endpoint and the id of this object,
        to be used to read details about this object or to delete it.
        """
        return urljoin(self.endpoint, '{}/'.format(self.uuid))

    def payload(self):
        """Return a dictionary for POST or PUT requests."""
        return {
            k: v for k, v in vars(self).items()
            if k not in ['uuid',
                         'client',
                         'endpoint',
                        ]
        }

    def update_payload(self):
        """Return a dictionary for POST or PUT requests."""
        return {
            k: v for k, v in vars(self).items()
            if k not in ['uuid',
                         'client',
                         'endpoint',
                         'cred_type',
                         'source_type'
                        ]
        }

    def to_str(self):
        """Return the string representation of the model."""
        return pformat(self.__dict__)

    def __repr__(self):
        """For `print` and `pprint`."""
        return self.to_str()

    def __ne__(self, other):
        """Return true if both objects are not equal."""
        return not self == other

    def create(self, **kwargs):
        """Send POST request to the self.endpoint of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            ``request.request()`` method.

        Sends ``self.payload()`` as the data of the POST request, thereby
        creating an object on the server.

        Before returning the requests.models.Response to the caller, the
        ``uuid`` of this object is set using the data from the response.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's ``self.uuid``.
        """
        response = self.client.post(self.endpoint, self.payload(), **kwargs)
        if response.status_code in range(200, 203):
            self.uuid = response.json().get('uuid')
        return response

    def list(self, **kwargs):
        """Send GET request to read all objects of this type.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response
            contains a list of dictionaries with the data associated with each
            object of this type stored on the server.
        """
        return self.client.get(self.endpoint, **kwargs)

    def read(self, **kwargs):
        """Send GET request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's `self.uuid`.
        """
        return self.client.get(self.path(), **kwargs)

    def update(self, **kwargs):
        """Send PUT request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        Sends `self.update_payload()` as the data of the PUT request, thereby
        updating the object on the server with the same `id` as this object
        with the fields contained in `self.update_payload()`.

        :returns: requests.models.Response. The json of this response contains
            the data associated with this object's `self.uuid`.
        """
        return self.client.put(self.path(), self.update_payload(), **kwargs)

    def delete(self, **kwargs):
        """Send DELETE request to the self.endpoint/{id} of this object.

        :param ``**kwargs``: Additional arguments accepted by Requests's
            `request.request()` method.

        :returns: requests.models.Response. A successful delete has the return
            code `204`.
        """
        return self.client.delete(self.path(), **kwargs)

    def reload(self):
        """Send a GET request based on the current uuid to reload the current member data"""
        if not self.uuid:
            raise KokuException(
                'Unable to refresh {} object. No uuid specified'.format(self.__class__))

        response = self.read()
        response_data = response.json()

        self_vars = self.payload()
        for key in response_data:
            if key in self_vars:
                setattr(self, key, response_data[key])

class KokuCustomer(KokuObject):
    """A class to create a Koku customer"""

    def __init__(self, client=None, uuid=None, name=None, owner=None):
        """
        Arguments:
            client - Existing `kokuqe.api.client` object to use for authentication.
                This client authentication will determine what koku features client has access to
            uuid - UUID of an existing customer
            name - Name of the customer
            owner - Customer owner information
                Dictionary Keys:
                    username - Username for the owner
                    email - Owner email address
                    password - Owner user password
        """
        super().__init__(client=client, uuid=uuid)
        self.endpoint = KOKU_CUSTOMER_PATH
        self.name = name
        self.owner = owner

class KokuUser(KokuObject):
    def __init__(self, client=None, uuid=None, username=None, email=None, password=None):
        """
        Arguments:
            client - Existing `kokuqe.api.client` object to use for authentication.
                This client authentication will determine what koku features client has access to
            uuid - UUID of an existing customer
            username - Username for the user
            email - User email address
            password - User password
        """
        super().__init__(client=client, uuid=uuid)
        self.endpoint = KOKU_USER_PATH
        self.username = username
        self.email = email
        self.password = password

    def get_current_user(self):
        """Send GET request return the user assigned to the client authentication token"""
        return self.client.get_user()
