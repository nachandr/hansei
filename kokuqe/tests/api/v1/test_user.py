import fauxfactory

from kokuqe.koku_models import Customer, User 

def test_crud_user(new_customer, new_user):
    """Create a new user, read the user data from the server and delete the user"""

    # All requests will throw an exception if response is an error code
    response = new_customer.create()

    # Login as the newly created customer user
    new_customer.client.login(
            username=new_customer.owner['username'], password=new_customer.owner['password'])


    # Use the customer client with token auth for the customer owner
    new_user.client.token = new_customer.client.token
    # All requests will throw an exception if response is an error code
    response = new_user.create()
    assert new_user.uuid, 'No uuid created for user'

    ##############################################
    #TODO: Implement test for update when koku api supports PUT
    ##############################################

    new_user.delete()
    response = new_user.list()

    response_results = response.json()['results']
    for user in response_results:
        assert user['uuid'] != new_user.uuid, "user was not deleted from the koku server"

    # Login as the admin user to delete the customer
    new_customer.client.login()
    new_customer.delete()
