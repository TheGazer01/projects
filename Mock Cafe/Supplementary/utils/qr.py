import qrcode
from PIL import Image

def make_qr(text, size=200):
    image = qrcode.make(text).convert("RGB")
    return image.resize((size, size), Image.NEAREST)