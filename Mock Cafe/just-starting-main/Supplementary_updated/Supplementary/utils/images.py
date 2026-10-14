import mimetypes
import re
from pathlib import Path

from PIL import Image, ImageOps

MENU_DIR = Path(__file__).resolve().parent.parent / "assets" / "menu"
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def slug(name):
    """'Cafe Latte' -> 'cafe-latte' (the file name to use in assets/menu)."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def find_menu_image(name):
    """Path of assets/menu/<slug>.png/.jpg/.webp/.svg for this item, or None."""
    for extension in EXTENSIONS:
        path = MENU_DIR / (slug(name) + extension)
        if path.is_file():
            return path
    return None


def load_menu_image(name, size=44):
    """A square, cropped picture for the desktop app (or None). SVGs are not loaded for desktop.
    Returns a PIL Image for supported raster formats, otherwise None for SVG.
    """
    path = find_menu_image(name)
    if path is None:
        return None
    if path.suffix.lower() == '.svg':
        # PIL often doesn't handle SVG without extra libs; let desktop skip SVGs
        return None
    try:
        picture = Image.open(path).convert("RGBA")
    except OSError:
        return None
    return ImageOps.fit(picture, (size, size), Image.Resampling.LANCZOS)


def content_type(path):
    name = str(path).lower()
    if name.endswith('.png'):
        return 'image/png'
    if name.endswith(('.jpg', '.jpeg')):
        return 'image/jpeg'
    if name.endswith('.webp'):
        return 'image/webp'
    if name.endswith('.svg'):
        return 'image/svg+xml'
    return 'application/octet-stream'
