from ..payment import Payment
from utils.formatting import php

class BankTransferPayment(Payment):

    def pay(self, amount):
        return f"Paid {php(amount)} using Bank Transfer."