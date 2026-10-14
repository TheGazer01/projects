from dataclasses import dataclass


@dataclass(frozen=True)
class Discount:
    name: str
    kind: str        # "percent" (value = % off) or "fixed" (value = pesos off)
    value: float

    def amount(self, subtotal):
        """How much this discount takes off the subtotal (never more than the subtotal)."""
        off = subtotal * self.value / 100 if self.kind == "percent" else self.value
        return round(min(max(off, 0), subtotal), 2)


# Add, remove or edit discounts here. Keep names short so they fit on the receipt.
DISCOUNTS = [
    Discount("Senior 20%", "percent", 20),
    Discount("PWD 20%", "percent", 20),
    Discount("Student 10%", "percent", 10),
    Discount("Promo PHP 50 off", "fixed", 50),
]


def find_discount(name):
    for discount in DISCOUNTS:
        if discount.name == name:
            return discount
    return None