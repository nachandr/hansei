"""Pytest customizations and fixtures for the koku tests."""
import fauxfactory
import pytest

from hansei import config
from hansei.koku_models import KokuServiceAdmin


@pytest.fixture(scope='function')
def koku_config():
    return config.get_config().get('koku', {})


@pytest.fixture(scope='function')
def service_admin(koku_config):
    return KokuServiceAdmin(username=koku_config.get('username'),
                            password=koku_config.get('password'))


class HanseiBaseTestAPI(object):
    @pytest.fixture(scope='class')
    def koku_config(self):
        return config.get_config().get('koku', {})

    @pytest.fixture(scope='class')
    def service_admin(self, koku_config):
        return KokuServiceAdmin(username=koku_config.get('username'),
                                password=koku_config.get('password'))

    @pytest.fixture(scope='class')
    def new_customer(self, service_admin):
        """Create a new KokuCustomer with random info"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        name = 'Customer {}'.format(uniq_string)
        owner = {
            'username': 'owner_{}'.format(uniq_string),
            'email': 'owner_{0}@{0}.com'.format(uniq_string),
            'password': 'redhat', }

        return service_admin.create_customer(name=name, owner=owner)

    @pytest.fixture(scope='class')
    def new_user(self, new_customer):
        """Create a new Koku user without authenticating to the server"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)

        if not new_customer.logged_in:
            new_customer.login()

        return new_customer.create_user(
            username='user_{}'.format(uniq_string),
            email='user_{0}@{0}.com'.format(uniq_string),
            password='redhat')

    @pytest.fixture(scope='class')
    def new_provider(self, new_user):
        """Create a new KokuProvider"""
        uniq_string = fauxfactory.gen_string('alphanumeric', 8)
        # Grab the first AWS provider
        provider_config = [
            prov for prov in config.get_config().
            get('providers', {})if prov['type'] == 'AWS'][0]

        if not new_user.logged_in:
            new_user.login()

        # TODO: Implement lazy authentication of the client for new
        # KokuObject() fixtures
        provider = new_user.create_provider(
            name='Provider {} for user {}'.format(
                uniq_string, new_user.username),
            authentication=provider_config.get('authentication'),
            provider_type=provider_config.get('type'),
            billing_source=provider_config.get('billing_source'))

        return provider
