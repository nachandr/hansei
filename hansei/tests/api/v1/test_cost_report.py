# -*- coding: utf-8 -*-
"""Tests for cost report API

The tests assume that the database is pre-populated with data including the
Koku default 'test_customer' customer by running 'make oc-create-test-db-file'.
"""
from hansei.koku_models import KokuCostReport, KokuCustomer

# Allowed deviation between the reported total cost and the summed up daily
# costs.
DEVIATION = 1


def test_validate_totalcost():
    """Test to validate the total cost.The total cost should be equal to the sum
    of all the daily costs"""

    sum = 0.0  # Total sum of daily costs

    # Login as test_customer
    customer = KokuCustomer(owner={'username': 'test_customer',
                            'password': 'str0ng!P@ss', 'email': 'foo@bar.com'})
    customer.login()
    report = KokuCostReport(customer.client)
    report.get()

    # Fetch daily costs and sum up the values
    for d in report.data:
        sum = sum + (d['total_cost'] if d['total_cost'] else 0.0)

    assert report.total['value'] - DEVIATION <= sum <= \
        report.total['value'] + DEVIATION, \
        'Report total is not equal to the sum of daily costs'
