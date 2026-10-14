# Endfield's Cafe - Point-of-Sale System

    pip install -r requirements.txt
    python main.py                      # desktop app
    python main.py --web                # website at http://localhost:8000
    python main.py --web --port 5000    # choose another port
    python main.py --web --host 0.0.0.0 # let phones/other PCs on your Wi-Fi open it

Custom logo: put your picture in `assets/logo.png` (jpg/webp/gif also work).
The window, receipts, PDF and website all use it. Delete it to go back to the built-in logo.

VAT: `VAT_RATE = 0.12` in `restaurant/order.py` (added on top of the subtotal).
