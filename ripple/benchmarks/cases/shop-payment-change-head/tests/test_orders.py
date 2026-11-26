from shop.orders import checkout


def test_checkout_paid():
    assert checkout([1, 2], "t")["status"] == "paid"
