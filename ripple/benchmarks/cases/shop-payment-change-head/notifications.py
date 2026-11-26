def send_receipt(receipt):
    return f"sent {receipt['status']}"


def send_marketing(user):
    handler = getattr(user, "notify")
    return handler()
