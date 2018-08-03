import fauxfactory
import pytest
import uuid

from hansei import config
from hansei.koku_models import KokuServiceAdmin
from requests.exceptions import HTTPError


@pytest.mark.smoke
class TestUserCrud(object):
    @pytest.fixture(scope='class')
    def service_admin(self):
        koku_config = config.get_config().get('koku', {})

        return KokuServiceAdmin(
            username=koku_config.get('username'), password=koku_config.get('password'))

    @pytest.fixture(scope='class')
    def customer(self, service_admin):
        """Create a new Koku customer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        #TODO: Implement lazy authentication of the client for new KokuObject()
        customer = service_admin.create_customer(name=name, owner=owner)
        customer.login()
        assert customer.uuid, 'No customer uuid created for customer'

        yield customer

        service_admin.delete_customer(customer.uuid)

    @pytest.fixture(scope='class')
    def user(self, customer):
        """Create a new Koku user without authenticating to the server"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)

        #TODO: Implement lazy authentication of the client for new KokuObject() fixtures
        user = customer.create_user(
            username='user_{}'.format(uniq_string),
            email='user_{0}@{0}.com'.format(uniq_string),
            password='redhat')

        return user

    def test_user_create(self, user):
        """Create a new user, read the user data from the server and delete the user"""
        # All requests will throw an exception if response is an error code
        assert user.uuid, 'No uuid created for user'

        assert  user.login(), "No token assigned to the user after login"

    def test_user_read(self, customer, user):
        server_user = customer.read_user(user.uuid)

        # TODO: Overload equivalence for KokuObjects
        assert server_user.uuid == user.uuid, 'User info cannot be read from the server'

        user_list = customer.list_users()
        assert len(user_list) > 0, 'No users available on server'

        user_uuid_list = [cust.uuid for cust in user_list]
        assert user.uuid in user_uuid_list, 'user uuid is not listed in the Koku server list'


    @pytest.mark.skip(reason="User update not implemented")
    def test_user_update(self):
        assert 0

    def test_user_update_preference(self, user):
        name = 'editor'
        preference = {name: 'vim', }

        orig_user_pref = user.read_preference().json()['results']

        pref_response = user.create_preference(name=name, preference=preference).json()
        assert pref_response['uuid'], 'New user preference was not assigned a uuid'

        assert pref_response['user']['uuid'] == user.uuid, (
                'Preference user uuid does not match the current user uuid')

        #TODO: Is string data normalized when saved. Case Normalization, localization, ...
        assert pref_response['name'] == name and pref_response['preference'] == preference, (
                'Created preference does not match the values supplied during creation')

        orig_pref_response = pref_response
        pref_description = 'There is no other editor choice'
        pref_response = user.update_preference(pref_response['uuid'], description=pref_description).json()

        assert (
            pref_response['description'] == pref_description and
            pref_response['description'] != orig_pref_response['description'] and
            pref_response['name'] == orig_pref_response['name'] and
            pref_response['preference'] == orig_pref_response['preference']), (
                'Preference was not updated properly')

    def test_user_delete(self, customer, user):
        customer.delete_user(user.uuid)
        user_list = customer.list_users()

        for server_user in user_list:
            assert server_user.uuid != user.uuid, "User was not deleted from the koku server"

    def test_user_create_no_username(self, customer):
        """Try to create a new user without username"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            customer.create_user(
                username='',
                email='user_{0}@{0}.com'.format(uniq_string),
                password='redhat')
        except HTTPError:
            pass

    def test_user_create_no_email(self, customer):
        """Try to create a new user without email"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            customer.create_user(
                username='user_{}'.format(uniq_string),
                email='',
                password='redhat')
        except HTTPError:
            pass

    def test_user_create_email_invalid_format(self, customer):
        """Try to create a new user with invalid email format"""
        # All requests will throw an exception if response is an error code

        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        try:
            customer.create_user(
                username='user_{}'.format(uniq_string),
                email='user_{0}{0}.com'.format(uniq_string),
                password='redhat')
        except HTTPError:
            pass

    def test_user_delete_invalid_uuid(self, customer):
        """Try to delete user with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            customer.delete_user(uuid.uuid1())
        except HTTPError:
            pass

    def test_user_get_invalid_uuid(self, customer):
        """Try to get user with invalid uuid"""
        # All requests will throw an exception if response is an error code

        try:
            customer.read_user(uuid.uuid1())
        except HTTPError:
            pass