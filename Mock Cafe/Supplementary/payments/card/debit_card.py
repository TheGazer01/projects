from ..payment import Payment
from utils.formatting import php


class DebitCardPayment(Payment):

    def pay(self, amount):
        return f"Paid {php(amount)} using Debit Card."