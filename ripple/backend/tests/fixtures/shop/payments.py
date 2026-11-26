def process_payment(order_total, token):
    if order_total <= 0:
        raise ValueError("invalid total")
    return {"status": "paid", "amount": order_total}


class Gateway:
    def charge(self, amount):
        return process_payment(amount, "tok")
