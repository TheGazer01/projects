from dataclasses import dataclass

# (size name, extra price added to the item's base price)
DRINK_SIZES = (("Small", 0.0), ("Medium", 20.0), ("Large", 40.0))


@dataclass(frozen=True)
class MenuItem:
    name: str
    category: str
    price: float                 # base price (the price of the first/smallest size)
    sizes: tuple = ()            # empty = no sizes, e.g. (("Small", 0), ("Large", 40))

    def resolve_size(self, size=None):
        """Return a valid size name for this item (None if it has no sizes)."""
        if not self.sizes:
            return None
        if size is None:
            return self.sizes[0][0]
        if size not in [label for label, _ in self.sizes]:
            raise ValueError(f"{self.name} does not come in size {size}.")
        return size

    def price_for(self, size=None):
        size = self.resolve_size(size)
        extra = dict(self.sizes).get(size, 0.0)
        return round(self.price + extra, 2)


class Menu:
    """Stores the restaurant's menu items (name, category, price, sizes)."""

    def __init__(self, items=None):
        self._items = list(items) if items is not None else self.default_items()

    @staticmethod
    def default_items():
        # Mock coffee shop menu for Endfield's Cafe. All names and prices are made up.
        # Keep item names at 20 characters or less so they fit on the receipt.
        # Add DRINK_SIZES as the 4th value to any item that comes in Small/Medium/Large.
        return [
            MenuItem("Iced Americano", "Coffee", 90.00, DRINK_SIZES),
            MenuItem("Cafe Latte", "Coffee", 110.00, DRINK_SIZES),
            MenuItem("Cappuccino", "Coffee", 110.00, DRINK_SIZES),
            MenuItem("Caramel Macchiato", "Coffee", 120.00, DRINK_SIZES),
            MenuItem("Spanish Latte", "Coffee", 115.00, DRINK_SIZES),
            MenuItem("Matcha Latte", "Non-Coffee", 120.00, DRINK_SIZES),
            MenuItem("Hot Chocolate", "Non-Coffee", 100.00, DRINK_SIZES),
            MenuItem("Milk Tea", "Non-Coffee", 80.00, DRINK_SIZES),
            MenuItem("Calamansi Juice", "Non-Coffee", 50.00, DRINK_SIZES),
            MenuItem("Bottled Water", "Non-Coffee", 35.00),
            MenuItem("Butter Croissant", "Food", 85.00),
            MenuItem("Blueberry Muffin", "Food", 60.00),
            MenuItem("Banana Bread", "Food", 60.00),
            MenuItem("Ham & Cheese Toastie", "Food", 120.00),
            MenuItem("Chicken Pesto Panini", "Food", 155.00),
            MenuItem("Extra Espresso Shot", "Add-ons", 40.00),
            MenuItem("Oat Milk Swap", "Add-ons", 35.00),
            MenuItem("Whipped Cream", "Add-ons", 20.00),
            MenuItem("Vanilla Syrup", "Add-ons", 20.00),
        ]

    def all_items(self):
        return list(self._items)

    def categories(self):
        seen = []
        for item in self._items:
            if item.category not in seen:
                seen.append(item.category)
        return seen

    def items_in(self, category):
        return [item for item in self._items if item.category == category]

    def find(self, name):
        for item in self._items:
            if item.name == name:
                return item
        return None