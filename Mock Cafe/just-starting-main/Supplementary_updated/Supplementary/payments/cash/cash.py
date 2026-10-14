from ..payment import Payment
from utils.formatting import php

class CashPayment(Payment):

    def pay(self, amount):
        return f"Paid {php(amount)} Using Cash."