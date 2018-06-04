import fauxfactory


def test_customer_crud(new_customer):
    """Create a new customer, read the customer data from the server and delete the customer"""

    # All requests will throw an exception if response is an error code
    response = new_customer.create()

    assert new_customer.uuid, 'No customer uuid created for customer'

    #TODO: Implement test for update when koku api supports PUT

    new_customer.delete()
    response = new_customer.list()

    response_results = response.json()['results']
    for cust in response_results:
        assert cust['uuid'] != new_customer.uuid, "Customer was not deleted from the koku server"
