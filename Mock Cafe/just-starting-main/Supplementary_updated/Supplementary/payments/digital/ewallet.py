from ..payment import Payment
from utils.formatting import php


class EWalletPayment(Payment):

    def pay(self, amount):
        return f"Paid {php(amount)} using E-Wallet."