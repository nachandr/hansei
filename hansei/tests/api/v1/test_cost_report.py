# -*- coding: utf-8 -*-
"""Tests for cost report API

The tests assume that the database is pre-populated with data.
"""
from hansei.koku_models import KokuCostReport, KokuCustomer


def test_validate_totalcost():
    """Test to validate the total cost.The total cost should be equal to the sum
    of all the daily costs"""

    sum = 0.0  # Total sum of daily costs

    # Login as test_customer
    customer = KokuCustomer(owner={'username': 'test_customer',
                            'password': 'str0ng!P@ss', 'email': 'foo@bar.com'})

    report = KokuCostReport.client(customer)
    customer.login()

    # Fetch daily costs and sum up the values
    for d in report.data():
        for key in d:
            if key == 'total_cost' and d[key] is not None:
                sum = sum + d[key]

    assert report.total['value'] == sum, \
        'Report total is not equal to the sum of daily costs'
