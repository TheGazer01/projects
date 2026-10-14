from datetime import datetime

from restaurant.order import VAT_RATE
from utils.formatting import php

WIDTH = 40


def _money(amount, peso=True):
    text = php(amount)
    return text if peso else text.replace("₱", "PHP ")


def _row(left, right):
    left = left[:max(WIDTH - len(right) - 1, 0)]
    return left + right.rjust(WIDTH - len(left))


class Receipt:
    """Prepares the receipt information and text for a finished transaction."""

    def __init__(self, business, address, cashier, number, order, total, method,
                 details=(), received=None, change=None, status="PAID", issued=None,
                 order_type=None, service=None):
        self.business = business
        self.address = address
        self.cashier = cashier
        self.number = number
        # Copy the order now so clearing the order later cannot change the receipt.
        self.items = [(line.item.name, line.size, line.quantity, line.unit_price, line.subtotal)
                      for line in order.lines]
        self.subtotal = order.subtotal()
        self.discount_name = order.discount.name if order.discount else None
        self.discount = order.discount_amount()
        self.vat = order.vat()
        self.total = total
        self.method = method
        self.details = list(details)
        self.received = received
        self.change = change
        self.status = status
        self.issued = issued or datetime.now()
        self.order_type = order_type
        self.service = service

    @property
    def number_text(self):
        return f"{self.number:06d}"

    @property
    def qr_payload(self):
        return (f"{self.business}|Receipt {self.number_text}|"
                f"Total {_money(self.total, False)}|{self.method}")

    def lines(self, peso=True):
        rule = "=" * WIDTH
        dash = "-" * WIDTH
        out = [
            rule,
            self.business.upper().center(WIDTH).rstrip(),
            "POINT OF SALE SYSTEM".center(WIDTH).rstrip(),
            self.address.center(WIDTH).rstrip(),
            rule,
            f"Receipt No.: {self.number_text}",
            f"Cashier: {self.cashier}",
            f"Date: {self.issued.strftime('%B %d, %Y')}",
            f"Time: {self.issued.strftime('%I:%M %p')}",
            dash,
            f"{'ITEM':<20}{'QTY':^6}{'AMOUNT':>14}",
            dash,
        ]
        for name, size, quantity, price, subtotal in self.items:
            out.append(f"{name[:20]:<20}{quantity:^6}{_money(subtotal, peso):>14}")
            prefix = f"{size} " if size else ""
            out.append(f"  {prefix}@ {_money(price, peso)} each")
        out += [dash, _row("Subtotal:", _money(self.subtotal, peso))]
        if self.discount_name:
            out.append(_row(f"Discount ({self.discount_name}):",
                            "-" + _money(self.discount, peso)))
        out += [
            _row(f"VAT ({VAT_RATE:.0%}):", _money(self.vat, peso)),
            _row("TOTAL:", _money(self.total, peso)),
            dash,
            _row("Payment Method:", self.method),
        ]
        if self.order_type:
            out.append(_row("Order Type:", self.order_type))
        if self.service:
            out.append(_row("Service:", self.service))
        for label, value in self.details:
            out.append(_row(f"{label}:", value))
        if self.received is not None:
            out.append(_row("Cash Received:", _money(self.received, peso)))
            out.append(_row("Change:", _money(self.change, peso)))
        out += [
            _row("Payment Status:", self.status),
            dash,
            "PAYMENT SUCCESSFUL".center(WIDTH).rstrip(),
            "THANK YOU!".center(WIDTH).rstrip(),
            rule,
        ]
        return out

    def text(self, peso=True):
        return "\n".join(self.lines(peso))