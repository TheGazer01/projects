from PIL import Image, ImageDraw, ImageFont

STYLES = {
    "Cash": ("CA", "#2ecc71"),
    "E-Wallet": ("EW", "#0d6efd"),
    "Credit Card": ("CC", "#f1ed00"),
    "Debit Card": ("DC", "#e67e22"),
    "Bank Transfer": ("BT", "#34495e"),
}


def make_icon(name, size=24):
    label, color = STYLES[name]
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=size // 5, fill=color)
    draw.text((size / 2, size / 2), label, fill="white",
              font=ImageFont.load_default(size=size // 2 - 1), anchor="mm")
    return image