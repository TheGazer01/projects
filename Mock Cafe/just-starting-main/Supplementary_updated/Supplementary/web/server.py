"""Website version of the POS. Uses only the Python standard library.

It reuses the same Menu, Order (12% VAT), payment classes and Receipt as the
desktop app, so the numbers always match.  Run it with:  python main.py --web
"""
import io
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from restaurant import Menu, Order, Receipt
from restaurant.discounts import DISCOUNTS, find_discount
from restaurant.order import VAT_RATE
from restaurant.payment_methods import METHODS
from utils.formatting import php
from utils.images import content_type, find_menu_image, slug
from utils.logo import make_logo
from utils.qr import make_qr
from utils.receipt import make_pos_receipt_pdf
from utils.report import METHOD_STYLE

INDEX = Path(__file__).with_name("index.html")
ASSETS = Path(__file__).resolve().parent.parent / "assets"


class POSState:
    """Everything the website remembers while the server is running."""

    def __init__(self, business, address, cashier):
        self.business, self.address, self.cashier = business, address, cashier
        self.menu = Menu()
        self.lock = threading.Lock()
        self.receipts = {}          # number -> Receipt
        self.history = []          # (payment class name, amount, result)

    def build_order(self, items, discount=None):
        order = Order()
        for entry in items:
            item = self.menu.find(str(entry.get("name", "")))
            if item is None:
                raise ValueError("That item is not on the menu.")
            order.add_item(item, entry.get("qty"), entry.get("size"))
        if discount:
            found = find_discount(discount)
            if found is None:
                raise ValueError("That discount does not exist.")
            order.set_discount(found)
        return order

    @staticmethod
    def totals(order):
        return {"subtotal": order.subtotal(), "discount": order.discount_amount(),
                "vat": order.vat(), "total": order.total(),
                "subtotal_text": php(order.subtotal()),
                "discount_text": "-" + php(order.discount_amount()) if order.discount else php(0),
                "vat_text": php(order.vat()), "total_text": php(order.total())}

    def checkout(self, items, method, value, discount=None, order_type=None, service=None):
        order = self.build_order(items, discount)
        if order.is_empty():
            raise ValueError("Please add at least one item to the order.")
        spec = next((m for m in METHODS if m.name == method), None)
        if spec is None:
            raise ValueError("Please select a payment method.")
        total = order.total()
        info = spec.validate(str(value), total)
        payment = spec.payment_class()
        result = payment.pay(total)
        with self.lock:
            number = len(self.history) + 1
            self.history.append((payment.__class__.__name__, total, result))
            receipt = Receipt(self.business, self.address, self.cashier, number, order,
                              total, spec.receipt_label, details=info.details,
                              received=info.received, change=info.change,
                              order_type=order_type, service=service)
            self.receipts[number] = receipt
        return {"number": number, "result": result, "text": receipt.text(),
                "qr": receipt.qr_payload, **self.totals(order),
                "order_type": order_type, "service": service}

    def stats(self):
        with self.lock:
            history = list(self.history)
        rows = []
        for key, (label, colour) in METHOD_STYLE.items():
            part = [h for h in history if h[0] == key]
            rows.append({"label": label, "colour": colour, "count": len(part),
                         "sales": round(sum(h[1] for h in part), 2)})
        sales = round(sum(h[1] for h in history), 2)
        return {"transactions": len(history), "sales": sales, "sales_text": php(sales),
                "methods": rows}


def make_handler(state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def _send(self, body, kind, status=200, extra=None):
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            for key, value in (extra or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data, status=200):
            self._send(json.dumps(data).encode(), "application/json", status)

        def _png(self, image):
            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            self._send(buffer.getvalue(), "image/png", extra={"Cache-Control": "max-age=3600"})

        def do_GET(self):
            url = urlparse(self.path)
            path = url.path
            if path == "/":
                self._send(INDEX.read_bytes(), "text/html; charset=utf-8")
            elif path == "/logo.png":
                self._png(make_logo(256))
            elif path == "/api/menu":
                self._json({
                    "business": state.business, "address": state.address,
                    "cashier": state.cashier, "vat_rate": VAT_RATE,
                    "methods": [{"name": m.name, "label": m.field_label, "hint": m.hint}
                                for m in METHODS],
                    "categories": [{"name": c, "items": [
                        {"name": i.name, "price": i.price, "price_text": php(i.price),
                         "image": f"/menu-img/{slug(i.name)}" if find_menu_image(i.name) else None,
                         "sizes": [{"label": label, "extra": extra} for label, extra in i.sizes]}
                        for i in state.menu.items_in(c)]} for c in state.menu.categories()],
                    "discounts": [d.name for d in DISCOUNTS],
                })
            elif path.startswith("/menu-img/"):
                image = find_menu_image(path[len("/menu-img/"):])
                if image is None:
                    return self._json({"error": "Not found."}, 404)
                self._send(image.read_bytes(), content_type(image),
                           extra={"Cache-Control": "max-age=300"})
            elif path.startswith("/assets/"):
                rel = path[len("/assets/"):]
                file = ASSETS / rel
                if not file.exists() or not file.is_file():
                    return self._json({"error": "Not found."}, 404)
                self._send(file.read_bytes(), content_type(file), extra={"Cache-Control": "max-age=300"})
            elif path == "/api/stats":
                self._json(state.stats())
            elif path == "/api/qr":
                text = parse_qs(url.query).get("text", [""])[0][:500]
                self._png(make_qr(text, 240))
            elif path.startswith("/api/receipt/") and path.endswith(".pdf"):
                try:
                    receipt = state.receipts[int(path[len("/api/receipt/"):-4])]
                except (ValueError, KeyError):
                    return self._json({"error": "Receipt not found."}, 404)
                buffer = io.BytesIO()
                make_pos_receipt_pdf(receipt.lines(peso=False), receipt.qr_payload, buffer)
                self._send(buffer.getvalue(), "application/pdf", extra={
                    "Content-Disposition": f'attachment; filename="receipt_{receipt.number_text}.pdf"'})
            else:
                self._json({"error": "Not found."}, 404)

        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(min(size, 100_000)) or b"{}")
                if self.path == "/api/quote":
                    return self._json(state.totals(state.build_order(
                        data.get("items", []), data.get("discount"))))
                if self.path == "/api/checkout":
                    return self._json(state.checkout(
                        data.get("items", []), data.get("method"), data.get("value", ""),
                        data.get("discount"), data.get("order_type"), data.get("service")))
                self._json({"error": "Not found."}, 404)
            except (ValueError, TypeError, AttributeError) as error:
                self._json({"error": str(error)}, 400)

    return Handler


def serve(business, address, cashier, host="127.0.0.1", port=8000, open_browser=True):
    state = POSState(business, address, cashier)
    server = ThreadingHTTPServer((host, port), make_handler(state))
    shown = "localhost" if host in ("127.0.0.1", "0.0.0.0") else host
    url = f"http://{shown}:{port}"
    print(f"{business} POS website running at {url}   (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
