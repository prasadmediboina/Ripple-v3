from .payments import process_payment


def refund(order_total):
    return process_payment(-order_total, "refund")
