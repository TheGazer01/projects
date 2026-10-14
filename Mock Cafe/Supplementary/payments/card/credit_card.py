from ..payment import Payment
from utils.formatting import php


class CreditCardPayment(Payment):

    def pay(self, amount):
        return f"Paid {php(amount)} using Credit Card."