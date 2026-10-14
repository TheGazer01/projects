import math
from pathlib import Path

from PIL import Image, ImageDraw

CARAMEL = "#c8863f"
ESPRESSO = "#2b1b12"
CREAM = "#f3e3c8"
ROAST = "#6b4226"

# Drop your own logo here (PNG/JPG/GIF/WEBP) and the whole app uses it:
# window icon, header, receipts, QR window and the website.
ASSETS = Path(__file__).resolve().parent.parent / "assets"
CUSTOM_NAMES = ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp", "logo.gif")


def custom_logo_path():
    for name in CUSTOM_NAMES:
        path = ASSETS / name
        if path.is_file():
            return path
    return None


def _draw_default(size):
    """Endfield's Cafe badge: a steaming cup with an 'E' on it (original artwork)."""
    s = 1024                                    # draw large, then shrink for smooth edges
    image = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.ellipse((16, 16, s - 16, s - 16), fill=CARAMEL)
    draw.ellipse((56, 56, s - 56, s - 56), fill=CREAM)
    draw.ellipse((84, 84, s - 84, s - 84), fill=ESPRESSO)

    for cx in (400, 512, 624):                  # steam
        points = [(cx + 28 * math.sin(t * 2 * math.pi), 440 - t * 190)
                  for t in (i / 30 for i in range(31))]
        draw.line(points, fill=CREAM, width=22, joint="curve")

    draw.arc((570, 540, 760, 730), start=-90, end=90, fill=CREAM, width=44)   # handle
    draw.rounded_rectangle((300, 500, 660, 780), radius=90, fill=CREAM)       # cup
    draw.rectangle((300, 500, 660, 600), fill=CREAM)
    draw.ellipse((300, 478, 660, 530), fill=ROAST, outline=CREAM, width=14)   # coffee
    draw.rounded_rectangle((250, 790, 710, 836), radius=23, fill=CARAMEL)     # saucer

    # the "E" on the cup, built from three bars and a stem
    draw.rectangle((434, 575, 470, 735), fill=ESPRESSO)
    for y in (575, 641, 699):
        draw.rectangle((434, y, 548, y + 36), fill=ESPRESSO)

    return image.resize((size, size), Image.Resampling.LANCZOS)


def _fit_custom(path, size):
    """Fit any picture into a transparent square without stretching it."""
    picture = Image.open(path).convert("RGBA")
    picture.thumbnail((size, size), Image.Resampling.LANCZOS)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(picture, ((size - picture.width) // 2, (size - picture.height) // 2), picture)
    return square


def make_logo(size=256):
    """Use assets/logo.* if it exists, otherwise the built-in badge."""
    path = custom_logo_path()
    if path is not None:
        try:
            return _fit_custom(path, size)
        except OSError:
            pass                                # unreadable file: fall back to the default
    return _draw_default(size)
