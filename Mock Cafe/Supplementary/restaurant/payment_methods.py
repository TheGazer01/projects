import math
import re
from dataclasses import dataclass
from typing import Callable

from payments import (
    CashPayment,
    EWalletPayment,
    CreditCardPayment,
    DebitCardPayment,
    BankTransferPayment,
)
from utils.formatting import php

MAX_CASH = 1_000_000


@dataclass(frozen=True)
class PaymentInfo:
    """What the cashier entered for a payment (mock data only)."""
    details: tuple = ()
    received: float | None = None
    change: float | None = None


def _digits(text):
    return re.sub(r"[\s-]", "", text)


def check_cash(text, total):
    try:
        received = round(float(text.strip().replace(",", "")), 2)
    except ValueError:
        raise ValueError("Please enter the cash received.") from None
    if not math.isfinite(received) or received > MAX_CASH:
        raise ValueError("Please enter a valid cash amount.")
    if received < total:
        raise ValueError("Insufficient payment.\n"
                         f"Please enter an amount equal to or greater than {php(total)}.")
    return PaymentInfo(received=received, change=round(received - total, 2))


def check_ewallet(text, total):
    number = _digits(text)
    if not re.fullmatch(r"09\d{9}", number):
        raise ValueError("Please enter a valid 11-digit GCash number (09XXXXXXXXX).")
    masked = number[:4] + "*" * 5 + number[-2:]
    return PaymentInfo(details=(("GCash No.", masked),))


def check_card(text, total):
    number = _digits(text)
    if not re.fullmatch(r"\d{16}", number):
        raise ValueError("Please enter a valid 16-digit card number.")
    return PaymentInfo(details=(("Card No.", f"**** **** **** {number[-4:]}"),))


def check_reference(text, total):
    reference = text.strip().upper()
    if not re.fullmatch(r"[A-Z0-9-]{6,20}", reference):
        raise ValueError("Please enter a valid reference number\n"
                         "(6 to 20 letters, numbers or dashes).")
    return PaymentInfo(details=(("Ref. No.", reference),))


@dataclass(frozen=True)
class MethodSpec:
    name: str                 # button text, also the icon name in utils.icons
    payment_class: type       # a subclass of payments.Payment
    receipt_label: str
    field_label: str
    hint: str
    validate: Callable


METHODS = [
    MethodSpec("Cash", CashPayment, "CASH",
               "Cash Received:", "Example: 500.00", check_cash),
    MethodSpec("E-Wallet", EWalletPayment, "E-WALLET (GCASH)",
               "GCash Number:", "Example: 09XXXXXXXXX", check_ewallet),
    MethodSpec("Credit Card", CreditCardPayment, "CREDIT CARD",
               "Card Number:", "Example: XXXX-XXXX-XXXX-XXXX", check_card),
    MethodSpec("Debit Card", DebitCardPayment, "DEBIT CARD",
               "Card Number:", "Example: XXXX-XXXX-XXXX-XXXX", check_card),
    MethodSpec("Bank Transfer", BankTransferPayment, "BANK TRANSFER",
               "Reference Number:", "Example: REF123456", check_reference),
]
