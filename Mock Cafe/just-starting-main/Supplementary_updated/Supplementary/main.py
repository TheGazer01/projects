import argparse

BUSINESS_NAME = "Endfield's Cafe"
ADDRESS = "Talos II, OMV Dijiang"
CASHIER = "Endministrator"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=f"{BUSINESS_NAME} Point-of-Sale System")
    parser.add_argument("--web", action="store_true",
                        help="run the website version instead of the desktop window")
    parser.add_argument("--port", type=int, default=8000, help="website port (default 8000)")
    parser.add_argument("--host", default="127.0.0.1",
                        help="use 0.0.0.0 to let other devices on your Wi-Fi open the site")
    parser.add_argument("--no-browser", action="store_true",
                        help="do not open the browser automatically")
    args = parser.parse_args()

    if args.web:
        from web.server import serve
        serve(BUSINESS_NAME, ADDRESS, CASHIER, args.host, args.port, not args.no_browser)
    else:
        from ui.pos import POSApp
        POSApp(BUSINESS_NAME, ADDRESS, CASHIER).run()
