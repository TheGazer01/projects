from dataclasses import dataclass

from utils.formatting import php

MAX_QUANTITY = 99
VAT_RATE = 0.05          # 12% VAT, charged on the price after any discount


@dataclass
class OrderLine:
    item: object
    quantity: int
    size: str | None = None

    @property
    def unit_price(self):
        return self.item.price_for(self.size)

    @property
    def key(self):
        """Unique name of this line, e.g. 'Cafe Latte (Large)'."""
        return f"{self.item.name} ({self.size})" if self.size else self.item.name

    @property
    def subtotal(self):
        return round(self.unit_price * self.quantity, 2)


class Order:
    """The cashier's current order: items, sizes, discount, VAT and total."""

    def __init__(self):
        self._lines = {}
        self.discount = None

    def add_item(self, item, quantity=1, size=None):
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
            raise ValueError("Please enter a whole number of at least 1 for the quantity.")
        line = OrderLine(item, quantity, item.resolve_size(size))
        current = self._lines[line.key].quantity if line.key in self._lines else 0
        if current + quantity > MAX_QUANTITY:
            raise ValueError(f"The quantity for one item cannot be more than {MAX_QUANTITY}.")
        if line.key in self._lines:
            self._lines[line.key].quantity += quantity
        else:
            self._lines[line.key] = line

    def remove_item(self, key):
        if key not in self._lines:
            raise KeyError(key)
        del self._lines[key]

    def set_discount(self, discount):
        self.discount = discount          # a Discount, or None for no discount

    def clear(self):
        self._lines.clear()
        self.discount = None

    @property
    def lines(self):
        return list(self._lines.values())

    def is_empty(self):
        return not self._lines

    def subtotal(self):
        return round(sum(line.subtotal for line in self._lines.values()), 2)

    def discount_amount(self):
        return self.discount.amount(self.subtotal()) if self.discount else 0.0

    def vat(self):
        return round((self.subtotal() - self.discount_amount()) * VAT_RATE, 2)

    def total(self):
        """Subtotal, minus discount, plus 12% VAT. This is what the customer pays."""
        return round(self.subtotal() - self.discount_amount() + self.vat(), 2)

    def display(self):
        if self.is_empty():
            return "No items in the order."
        rows = []
        for line in self.lines:
            rows.append(line.key)
            rows.append(f"{php(line.unit_price)} × {line.quantity} = {php(line.subtotal)}")
        rows.append("-" * 25)
        rows.append(f"SUBTOTAL = {php(self.subtotal())}")
        if self.discount:
            rows.append(f"DISCOUNT ({self.discount.name}) = -{php(self.discount_amount())}")
        rows.append(f"VAT ({VAT_RATE:.0%}) = {php(self.vat())}")
        rows.append(f"TOTAL = {php(self.total())}")
        return "\n".join(rows)