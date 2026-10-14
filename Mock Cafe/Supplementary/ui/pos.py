import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import ttkbootstrap as ttk
from PIL import ImageTk

from restaurant import Menu, Order, Receipt
from restaurant.discounts import DISCOUNTS, find_discount
from restaurant.order import VAT_RATE
from ui import theme
from ui.payment_dialog import PaymentDialog
from ui.receipt_window import ReceiptWindow
from ui.widgets import MenuCard
from utils.formatting import php
from utils.images import load_menu_image
from utils.logo import make_logo
from utils.qr import make_qr
from utils.report import export_csv, show_chart
from utils.console import log_payment, show_history

FONT = theme.FONT

CATEGORY_ICONS = {"Coffee": "☕", "Non-Coffee": "🧋", "Food": "🥐", "Add-ons": "➕"}


class POSApp:
    NO_DISCOUNT = "No discount"

    def __init__(self, business_name, address, cashier, color=theme.ESPRESSO, menu=None):
        self.business_name = business_name
        self.address = address
        self.cashier = cashier
        self.color = color

        self.menu = menu or Menu()
        self.order = Order()
        self.history = []
        self.receipt_count = 0
        self.sales_total = 0.0
        self.selected_item = None
        self.item_buttons = {}
        self.menu_photos = []
        self.chip_buttons = {}
        self.category_pages = {}

        self.window = ttk.Window(themename="cosmo")
        self.window.title(f"{self.business_name} - Point-of-Sale System")
        self.window.geometry("1300x760")
        self.window.minsize(1180, 700)
        self.window.configure(background=theme.CREAM)
        self.window.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.order_type_var = tk.StringVar(value="Takeout")
        self.service_var = tk.StringVar(value="Counter Pickup")

        self.qty_var = tk.StringVar(value="1")
        self.size_var = tk.StringVar()
        self.discount_var = tk.StringVar(value=self.NO_DISCOUNT)
        self.discount_amt_var = tk.StringVar()
        self.total_var = tk.StringVar()
        self.subtotal_var = tk.StringVar()
        self.vat_var = tk.StringVar()
        self.selected_var = tk.StringVar(value="Tap an item to select it")
        self.count_var = tk.StringVar()
        self.sales_var = tk.StringVar()
        self.clock_var = tk.StringVar()

        theme.apply_styles(ttk.Style())
        self._build_menubar()
        self._build_header()
        self._build_body()
        self.refresh_order()
        self.refresh_sales()
        self._tick()

    def run(self):
        self.window.mainloop()

    def _panel(self, parent, title, column, padx):
        outer = tk.Frame(parent, bg=theme.CARD, highlightbackground=theme.LINE,
                         highlightthickness=1)
        outer.grid(row=0, column=column, sticky="nsew", padx=padx)
        ttk.Label(outer, text=title, style="Title.TLabel", foreground=theme.ROAST
                  ).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Frame(outer, bg=theme.LINE, height=1).pack(fill="x", padx=16)
        inner = ttk.Frame(outer, style="Card.TFrame", padding=(16, 12))
        inner.pack(fill="both", expand=True)
        return inner

    def _build_menubar(self):
        menubar = tk.Menu(self.window)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New Transaction", command=self.new_transaction_button)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Sales Report (Chart)", command=self.show_chart)
        reports_menu.add_command(label="Export Sales to CSV", command=self.export)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        self.window.configure(menu=menubar)

    def _build_header(self):
        header = ttk.Frame(self.window, style="Header.TFrame", padding=(24, 12))
        header.pack(side="top", fill="x")

        self.logo_image = ImageTk.PhotoImage(make_logo(64))
        self.window.iconphoto(True, self.logo_image)
        ttk.Label(header, image=self.logo_image, style="Header.TLabel").pack(
            side="left", padx=(0, 16))

        text = ttk.Frame(header, style="Header.TFrame")
        text.pack(side="left")
        ttk.Label(text, text=self.business_name.upper(), style="Header.TLabel",
                  font=(FONT, 20, "bold")).pack(anchor="w")
        ttk.Label(text, text=f"Point-of-Sale System   |   {self.address}",
                  style="Header.TLabel", foreground=theme.CARAMEL,
                  font=(FONT, 10)).pack(anchor="w")

        right = ttk.Frame(header, style="Header.TFrame")
        right.pack(side="right")
        ttk.Label(right, textvariable=self.clock_var, style="Header.TLabel",
                  font=(FONT, 16, "bold")).pack(anchor="e")
        ttk.Label(right, text=f"Cashier: {self.cashier}", style="Header.TLabel",
                  foreground=theme.CARAMEL, font=(FONT, 10)).pack(anchor="e")

    def _tick(self):
        self.clock_var.set(datetime.now().strftime("%a, %b %d   %I:%M %p"))
        self.window.after(30000, self._tick)

    def _build_body(self):
        body = ttk.Frame(self.window, style="Cream.TFrame", padding=(20, 16, 20, 20))
        body.pack(side="top", fill="both", expand=True)
        body.columnconfigure(0, weight=6, uniform="area")
        body.columnconfigure(1, weight=5, uniform="area")
        body.columnconfigure(2, weight=4, uniform="area")
        body.rowconfigure(0, weight=1)

        self._build_menu_area(self._panel(body, "MENU", 0, (0, 8)))
        self._build_order_area(self._panel(body, "CURRENT ORDER", 1, (8, 8)))
        self._build_transaction_area(self._panel(body, "TRANSACTION", 2, (8, 0)))

    def _build_menu_area(self, area):
        chips = ttk.Frame(area, style="Card.TFrame")
        chips.pack(fill="x", pady=(0, 12))
        pages = ttk.Frame(area, style="Card.TFrame")
        pages.pack(fill="both", expand=True)
        pages.rowconfigure(0, weight=1)
        pages.columnconfigure(0, weight=1)

        for category in self.menu.categories():
            icon = CATEGORY_ICONS.get(category, "")
            chip = ttk.Button(chips, text=f"{icon} {category}".strip(), style="Chip.TButton",
                              command=lambda c=category: self.show_category(c))
            chip.pack(side="left", padx=(0, 8))
            self.chip_buttons[category] = chip

            page = ttk.Frame(pages, style="Card.TFrame")
            page.grid(row=0, column=0, sticky="nsew")
            for col in (0, 1):
                page.columnconfigure(col, weight=1, uniform="card")
            items = self.menu.items_in(category)
            for index, item in enumerate(items):
                row_index = index // 2
                page.rowconfigure(row_index, weight=1, uniform="cardrow")
                price_text = ("from " if item.sizes else "") + php(item.price)
                picture = load_menu_image(item.name, 44)
                photo = ImageTk.PhotoImage(picture) if picture else None
                if photo:
                    self.menu_photos.append(photo)
                card = MenuCard(page, item.name, price_text,
                                lambda i=item: self.select_item(i), photo)
                card.grid(row=row_index, column=index % 2, sticky="nsew", padx=5, pady=5)
                self.item_buttons[item.name] = card
            self.category_pages[category] = page

        tk.Frame(area, bg=theme.LINE, height=1).pack(fill="x", pady=(10, 10))
        ttk.Label(area, textvariable=self.selected_var, style="Title.TLabel",
                  wraplength=360, justify="left").pack(anchor="w")

        self.size_row = ttk.Frame(area, style="Card.TFrame")
        self.size_row.pack(fill="x", pady=(8, 0))

        row = ttk.Frame(area, style="Card.TFrame")
        row.pack(fill="x", pady=(10, 0))
        ttk.Label(row, text="Quantity", style="Card.TLabel").pack(side="left")
        ttk.Button(row, text="-", style="Small.TButton", width=3,
                   command=lambda: self.change_qty(-1)).pack(side="left", padx=(12, 4))
        entry = ttk.Entry(row, width=4, textvariable=self.qty_var, justify="center",
                          font=(FONT, 12, "bold"))
        entry.pack(side="left", ipady=3)
        entry.bind("<Return>", lambda event: self.add_to_order())
        ttk.Button(row, text="+", style="Small.TButton", width=3,
                   command=lambda: self.change_qty(1)).pack(side="left", padx=(4, 0))
        ttk.Button(row, text="ADD TO ORDER", style="Accent.TButton",
                   command=self.add_to_order).pack(side="right", ipady=4)

        categories = self.menu.categories()
        if categories:
            self.show_category(categories[0])

    def _build_order_area(self, area):
        table = ttk.Frame(area, style="Card.TFrame")
        table.pack(fill="both", expand=True)
        columns = ("item", "qty", "price", "subtotal")
        self.order_tree = ttk.Treeview(table, columns=columns, show="headings",
                                       selectmode="browse", height=8)
        for column, heading, width, anchor in [
            ("item", "Item", 150, "w"),
            ("qty", "Qty", 44, "center"),
            ("price", "Price", 80, "e"),
            ("subtotal", "Subtotal", 90, "e"),
        ]:
            self.order_tree.heading(column, text=heading, anchor=anchor)
            self.order_tree.column(column, width=width, anchor=anchor,
                                   stretch=(column == "item"))
        self.order_tree.tag_configure("odd", background="#fbf6ee")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.order_tree.pack(side="left", fill="both", expand=True)

        buttons = ttk.Frame(area, style="Card.TFrame")
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Remove Selected", style="Danger.TButton",
                   command=self.remove_selected).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(buttons, text="Clear Order", style="Ghost.TButton",
                   command=self.clear_order).pack(side="left", expand=True, fill="x", padx=(4, 0))

        discount_row = ttk.Frame(area, style="Card.TFrame")
        discount_row.pack(fill="x", pady=(12, 0))
        ttk.Label(discount_row, text="Discount", style="Card.TLabel").pack(side="left")
        self.discount_box = ttk.Combobox(
            discount_row, textvariable=self.discount_var, state="readonly",
            values=[self.NO_DISCOUNT] + [d.name for d in DISCOUNTS])
        self.discount_box.pack(side="right", fill="x", expand=True, padx=(12, 0))
        self.discount_box.bind("<<ComboboxSelected>>", lambda event: self.apply_discount())

        totals = ttk.Frame(area, style="Stat.TFrame", padding=(16, 12))
        totals.pack(fill="x", pady=(8, 0))
        totals.columnconfigure(1, weight=1)
        for row, (label, var) in enumerate([
                ("Subtotal", self.subtotal_var),
                ("Discount", self.discount_amt_var),
                (f"VAT ({VAT_RATE:.0%})", self.vat_var)]):
            ttk.Label(totals, text=label, style="Stat.TLabel").grid(
                row=row, column=0, sticky="w", pady=(0 if row == 0 else 4, 0))
            ttk.Label(totals, textvariable=var, style="Stat.TLabel").grid(
                row=row, column=1, sticky="e", pady=(0 if row == 0 else 4, 0))
        tk.Frame(totals, bg=theme.LINE, height=1).grid(row=3, column=0, columnspan=2,
                                                      sticky="ew", pady=8)
        ttk.Label(totals, text="TOTAL", style="Stat.TLabel",
                  font=(FONT, 12, "bold")).grid(row=4, column=0, sticky="w")
        ttk.Label(totals, textvariable=self.total_var, style="Stat.TLabel",
                  font=(FONT, 16, "bold")).grid(row=4, column=1, sticky="e")

    def _build_transaction_area(self, area):
        due = ttk.Frame(area, style="Stat.TFrame", padding=(14, 12))
        due.pack(fill="x")
        ttk.Label(due, text="AMOUNT DUE", style="StatMuted.TLabel").pack(anchor="w")
        ttk.Label(due, textvariable=self.total_var, style="Stat.TLabel",
                  font=(FONT, 20, "bold"), foreground=theme.GREEN).pack(anchor="w")
        ttk.Label(due, text=f"incl. {VAT_RATE:.0%} VAT", style="StatMuted.TLabel").pack(anchor="w")

        types = ttk.Frame(area, style="Card.TFrame")
        types.pack(fill="x", pady=(12, 0))
        ttk.Label(types, text="Order:", style="Card.TLabel").pack(side="left")
        ttk.Radiobutton(types, text="Takeout", value="Takeout", variable=self.order_type_var).pack(side="left", padx=6)
        ttk.Radiobutton(types, text="Dine-in", value="Dine-in", variable=self.order_type_var).pack(side="left", padx=6)

        svc = ttk.Frame(area, style="Card.TFrame")
        svc.pack(fill="x", pady=(8, 0))
        ttk.Label(svc, text="Service:", style="Card.TLabel").pack(side="left")
        ttk.Radiobutton(svc, text="Counter Pickup", value="Counter Pickup", variable=self.service_var).pack(side="left", padx=6)
        ttk.Radiobutton(svc, text="Table Service", value="Table Service", variable=self.service_var).pack(side="left", padx=6)

        ttk.Button(area, text="PROCEED TO PAYMENT", style="Go.TButton",
                   command=self.proceed_to_payment).pack(fill="x", pady=(12, 6))
        ttk.Button(area, text="New Transaction", style="Ghost.TButton",
                   command=self.new_transaction_button).pack(fill="x")

        stats = ttk.Frame(area, style="Stat.TFrame", padding=(14, 10))
        stats.pack(fill="x", pady=(14, 0))
        ttk.Label(stats, text="TODAY", style="StatMuted.TLabel").pack(anchor="w")
        ttk.Label(stats, textvariable=self.count_var, style="Stat.TLabel").pack(anchor="w")
        ttk.Label(stats, textvariable=self.sales_var, style="Stat.TLabel",
                  font=(FONT, 12, "bold")).pack(anchor="w")

        ttk.Label(area, text="Latest receipt", style="Muted.TLabel").pack(anchor="w", pady=(14, 4))
        qr_holder = ttk.Frame(area, style="Card.TFrame", width=110, height=110)
        qr_holder.pack(anchor="w")
        qr_holder.pack_propagate(False)
        self.qr_label = ttk.Label(qr_holder, text="No QR yet", style="Muted.TLabel",
                                  anchor="center")
        self.qr_label.pack(expand=True)

        ttk.Button(area, text="Exit", style="Danger.TButton",
                   command=self.exit_app).pack(side="bottom", fill="x", pady=(6, 0))
        reports = ttk.Frame(area, style="Card.TFrame")
        reports.pack(side="bottom", fill="x")
        ttk.Button(reports, text="Chart", style="Ghost.TButton",
                   command=self.show_chart).pack(side="left", expand=True, fill="x", padx=(0, 3))
        ttk.Button(reports, text="Export", style="Ghost.TButton",
                   command=self.export).pack(side="left", expand=True, fill="x", padx=(3, 0))

    def show_category(self, category):
        page = self.category_pages.get(category)
        if page:
            page.tkraise()
        for name, chip in self.chip_buttons.items():
            chip.configure(style="ChipOn.TButton" if name == category else "Chip.TButton")

    def select_item(self, item):
        self.selected_item = item
        self.size_var.set(item.resolve_size() or "")
        for name, card in self.item_buttons.items():
            card.set_selected(name == item.name)
        self.draw_sizes()
        self.update_selected_label()

    def draw_sizes(self):
        for child in self.size_row.winfo_children():
            child.destroy()
        item = self.selected_item
        if item is None or not item.sizes:
            return
        ttk.Label(self.size_row, text="Size", style="Card.TLabel").pack(side="left")
        for label, _extra in item.sizes:
            on = label == self.size_var.get()
            ttk.Button(self.size_row, text=f"{label} {php(item.price_for(label))}",
                       style="SizeOn.TButton" if on else "Size.TButton",
                       command=lambda l=label: self.choose_size(l)
                       ).pack(side="left", padx=(6, 0))

    def choose_size(self, label):
        self.size_var.set(label)
        self.draw_sizes()
        self.update_selected_label()

    def update_selected_label(self):
        item = self.selected_item
        if item is None:
            self.selected_var.set("Tap an item to select it")
            return
        size = self.size_var.get() or None
        name = f"{item.name}, {size}" if size else item.name
        self.selected_var.set(f"Selected: {name} ({php(item.price_for(size))})")

    def apply_discount(self):
        self.order.set_discount(find_discount(self.discount_var.get()))
        self.refresh_order()

    def change_qty(self, step):
        try:
            current = int(self.qty_var.get())
        except ValueError:
            current = 1
        self.qty_var.set(str(min(99, max(1, current + step))))

    def show_chart(self):
        show_chart(self.window, self.history, self.logo_image)

    def add_to_order(self):
        if self.selected_item is None:
            messagebox.showerror("No Item Selected", "Please select a menu item first.")
            return
        try:
            quantity = int(self.qty_var.get())
        except ValueError:
            messagebox.showerror("Invalid Quantity",
                                 "Please enter a whole number for the quantity.")
            return
        try:
            self.order.add_item(self.selected_item, quantity, self.size_var.get() or None)
        except ValueError as error:
            messagebox.showerror("Invalid Quantity", str(error))
            return
        self.qty_var.set("1")
        self.refresh_order()

    def remove_selected(self):
        selection = self.order_tree.selection()
        if not selection:
            messagebox.showerror("Nothing Selected",
                                 "Please select an item in the order to remove.")
            return
        for iid in selection:
            self.order.remove_item(iid)
        self.refresh_order()

    def clear_order(self):
        if self.order.is_empty():
            return
        if messagebox.askyesno("Clear Order", "Remove all items from the current order?"):
            self.order.clear()
            self.refresh_order()

    def refresh_order(self):
        self.order_tree.delete(*self.order_tree.get_children())
        for index, line in enumerate(self.order.lines):
            self.order_tree.insert("", "end", iid=line.key,
                                   tags=("odd",) if index % 2 else (), values=(
                    line.key, line.quantity, php(line.unit_price), php(line.subtotal)))
        discount = self.order.discount
        self.discount_var.set(discount.name if discount else self.NO_DISCOUNT)
        self.discount_amt_var.set(f"-{php(self.order.discount_amount())}" if discount else php(0))
        self.subtotal_var.set(php(self.order.subtotal()))
        self.vat_var.set(php(self.order.vat()))
        self.total_var.set(php(self.order.total()))

    def show_qr(self, receipt):
        self.qr_image = ImageTk.PhotoImage(make_qr(receipt.qr_payload, 104))
        self.qr_label.configure(image=self.qr_image, text="")

    def refresh_sales(self):
        self.count_var.set(f"Transactions: {self.receipt_count}")
        self.sales_var.set(f"Sales: {php(self.sales_total)}")

    def proceed_to_payment(self):
        if self.order.is_empty():
            messagebox.showerror("No Order", "Please add at least one item to the order.")
            return
        discount = (f"  -  Discount {php(self.order.discount_amount())}"
                    if self.order.discount else "")
        PaymentDialog(self.window, self.order.total(), self.process_payment,
                      note=f"Subtotal {php(self.order.subtotal())}{discount}  +  "
                           f"VAT {VAT_RATE:.0%} {php(self.order.vat())}")

    def process_payment(self, payment, spec, info):
        amount = self.order.total()
        try:
            result = payment.pay(amount)
        except Exception as error:
            messagebox.showerror("Payment Failed", str(error))
            return False

        self.receipt_count += 1
        self.sales_total += amount
        self.history.append((payment.__class__.__name__, amount, result))
        log_payment(self.receipt_count, result)

        receipt = Receipt(
            self.business_name, self.address, self.cashier, self.receipt_count,
            self.order, amount, spec.receipt_label,
            details=info.details, received=info.received, change=info.change,
            order_type=self.order_type_var.get(), service=self.service_var.get(),
        )
        self.refresh_sales()
        self.show_qr(receipt)
        ReceiptWindow(self.window, receipt, result, self.reset_order, self.logo_image)
        return True

    def reset_order(self):
        self.order.clear()
        self.qty_var.set("1")
        self.refresh_order()

    def new_transaction_button(self):
        if not self.order.is_empty() and not messagebox.askyesno(
                "New Transaction", "Clear the current order and start a new transaction?"):
            return
        self.reset_order()

    def export(self):
        if not self.history:
            messagebox.showinfo("Nothing to Export", "Complete a payment first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")]
        )
        if path:
            export_csv(self.history, path)
            messagebox.showinfo("Exported", f"Saved to {path}")

    def exit_app(self):
        if not self.order.is_empty() and not messagebox.askyesno(
                "Exit", "There is an unpaid order. Exit anyway?"):
            return
        show_history(self.history)
        self.window.destroy()