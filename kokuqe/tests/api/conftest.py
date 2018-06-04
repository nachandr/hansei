"""Pytest customizations and fixtures for the quipucords tests."""
import fauxfactory
import pytest

from kokuqe import config
from kokuqe.koku_models import Customer 

@pytest.fixture
def koku_config():
    return config.get_config().get('koku', {})

@pytest.fixture
def new_customer():
    uniq_string = fauxfactory.gen_string('alphanumeric', 8)
    name='Customer {}'.format(uniq_string)
    owner={
        'username': 'user_{}'.format(uniq_string),
        'email': 'user_{0}@{0}.com'.format(uniq_string),
        'password': uniq_string, }

    return Customer(name=name, owner=owner)

