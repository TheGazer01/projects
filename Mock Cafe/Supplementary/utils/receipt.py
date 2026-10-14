from PIL import Image, ImageDraw, ImageFont

from utils.logo import make_logo
from utils.qr import make_qr
from utils.formatting import php


def _font(size, bold=False):
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    names += ["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _money(amount):
    # "PHP" is used in the PDF so the peso sign never renders as a blank box.
    return php(amount).replace("\u20b1", "PHP ")


def make_receipt_pdf(data, path):
    width, margin = 600, 40
    image = Image.new("RGB", (width, 1400), "white")
    draw = ImageDraw.Draw(image)
    body, bold, big = _font(20), _font(20, True), _font(30, True)
    y = 40

    def centered(text, font):
        nonlocal y
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((width - (box[2] - box[0])) / 2, y), text, fill="black", font=font)
        y += (box[3] - box[1]) + 14

    def rule():
        nonlocal y
        draw.line((margin, y, width - margin, y), fill="#999999", width=2)
        y += 16

    def row(left, right, font=body):
        nonlocal y
        draw.text((margin, y), left, fill="black", font=font)
        box = draw.textbbox((0, 0), right, font=font)
        draw.text((width - margin - (box[2] - box[0]), y), right, fill="black", font=font)
        y += 32

    centered(data["business"].upper(), big)
    centered("PAYMENT RECEIPT", body)
    rule()
    row("Receipt No.:", data["number"])
    row("Date:", data["date"])
    row("Time:", data["time"])
    row("Payer:", data["payer"])
    rule()
    row("Payment Method:", data["method"])
    row("Amount Due:", _money(data["amount"]))
    if data["tendered"] is not None:
        row("Cash Tendered:", _money(data["tendered"]))
        row("Change:", _money(data["change"]))
    rule()
    row("TOTAL:", _money(data["amount"]), bold)
    y += 10
    centered("PAYMENT SUCCESSFUL", bold)
    y += 10

    qr = make_qr(f"{data['business']}\n{data['number']}\n{data['result']}", 220)
    image.paste(qr, ((width - 220) // 2, y))
    y += 220 + 20
    centered("Scan for your receipt", body)
    centered("THANK YOU!", bold)

    image = image.crop((0, 0, width, y + 30))
    image.save(path, "PDF", resolution=150)

def _mono_font(size):
    for name in ("consola.ttf", "DejaVuSansMono.ttf", "cour.ttf", "LiberationMono-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def make_pos_receipt_pdf(lines, qr_text, path):
    """Save the POS receipt text (and a QR code) as a one-page PDF."""
    font = _mono_font(22)
    margin, line_height, qr_size = 40, 30, 220
    char_width = font.getlength("M")
    width = int(char_width * max(len(line) for line in lines)) + margin * 2
    logo_size = 110
    height = margin * 2 + logo_size + 20 + line_height * len(lines) + qr_size + 70

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    logo = make_logo(logo_size)
    image.paste(logo, ((width - logo_size) // 2, margin), logo)
    y = margin + logo_size + 20
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += line_height

    y += 10
    image.paste(make_qr(qr_text, qr_size), ((width - qr_size) // 2, y))
    y += qr_size + 10
    caption = "Scan for your receipt"
    box = draw.textbbox((0, 0), caption, font=font)
    draw.text(((width - (box[2] - box[0])) / 2, y), caption, fill="black", font=font)
    image.save(path, "PDF", resolution=150)
