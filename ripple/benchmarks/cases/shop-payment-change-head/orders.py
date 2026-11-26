from shop.payments import process_payment
from shop import notifications


def create_order(cart, token):
    total = sum(cart)
    receipt = process_payment(total, token)
    notifications.send_receipt(receipt)
    return receipt


def checkout(cart, token):
    return create_order(cart, token)
