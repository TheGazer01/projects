import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime
import ttkbootstrap as ttk
from PIL import ImageTk

from payments import (
    CashPayment,
    EWalletPayment,
    CreditCardPayment,
    DebitCardPayment,
    BankTransferPayment,
)
from utils.icons import make_icon
from utils.qr import make_qr
from utils.formatting import php
from utils.receipt import make_receipt_pdf
from utils.report import export_csv, show_chart
from utils.console import log_payment, show_history


class PaymentApp:
    PAYMENT_METHODS = [
        ("Cash", CashPayment),
        ("E-Wallet", EWalletPayment),
        ("Credit Card", CreditCardPayment),
        ("Debit Card", DebitCardPayment),
        ("Bank Transfer", BankTransferPayment),
    ]

    def __init__(self, business_name="My Business", color="#1a56db"):
        self.business_name = business_name
        self.color = color

        self.history = []
        self.last_receipt = {}
        self.selected = {"name": None, "class": None}
        self.icons = []
        self.method_buttons = {}

        self.window = ttk.Window(themename="cosmo")
        self.window.title(self.business_name)
        self.window.geometry("680x780")
        self.window.minsize(640, 720)
        self.window.configure(background=self.color)

        self._build_styles()
        self._build_header()
        self._build_footer()
        self._build_card()
        self._build_details()
        self._build_receipt_panel()
        self._build_log()
        self.select_method("Cash", CashPayment)

    def run(self):
        self.window.mainloop()

    # ------------------------------------------------------------ layout
    def _build_styles(self):
        style = ttk.Style()
        style.configure("Blue.TFrame", background=self.color)
        style.configure("Blue.TLabel", background=self.color, foreground="white")
        style.configure("Card.TFrame", background="white")
        style.configure("Card.TLabel", background="white", foreground="#1f2937")
        style.configure("Card.TLabelframe", background="white", bordercolor="#c9ced6")
        style.configure("Card.TLabelframe.Label", background="white",
                        foreground="#1f2937", font=("Segoe UI", 9))

    def _build_header(self):
        header = ttk.Frame(self.window, style="Blue.TFrame")
        header.pack(side="top", pady=(20, 12))
        ttk.Label(header, text=self.business_name.upper(), style="Blue.TLabel",
                  font=("Segoe UI", 22, "bold")).pack()
        ttk.Label(header, text="Payment System", style="Blue.TLabel",
                  font=("Segoe UI", 10)).pack()

    def _build_footer(self):
        footer = ttk.Frame(self.window, style="Blue.TFrame")
        footer.pack(side="bottom", fill="x", padx=20, pady=15)
        for text, command in [
            ("Chart", lambda: show_chart(self.window, self.history)),
            ("Export", self.export),
            ("Exit", self.exit_app),
        ]:
            ttk.Button(footer, text=text, bootstyle="light",
                       command=command).pack(side="left", expand=True, fill="x", padx=4)

    def _build_card(self):
        self.card = ttk.Frame(self.window, style="Card.TFrame", padding=15)
        self.card.pack(side="top", fill="both", expand=True, padx=20)

    def _build_details(self):
        details = ttk.Labelframe(self.card, text="Payment Details",
                                 style="Card.TLabelframe", padding=15)
        details.pack(fill="x")
        details.columnconfigure(1, weight=1)

        ttk.Label(details, text="Payer name", style="Card.TLabel").grid(
            row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(details)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=(15, 0), pady=5)

        ttk.Label(details, text="Amount due (PHP)", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=5)
        self.amount_entry = ttk.Entry(details)
        self.amount_entry.grid(row=1, column=1, sticky="ew", padx=(15, 0), pady=5)

        ttk.Label(details, text="Payment method", style="Card.TLabel").grid(
            row=2, column=0, sticky="nw", pady=8)
        method_frame = ttk.Frame(details, style="Card.TFrame")
        method_frame.grid(row=2, column=1, sticky="ew", padx=(15, 0))
        for column in range(3):
            method_frame.columnconfigure(column, weight=1, uniform="method")

        for index, (name, payment_class) in enumerate(self.PAYMENT_METHODS):
            icon = ImageTk.PhotoImage(make_icon(name))
            self.icons.append(icon)
            button = ttk.Button(
                method_frame,
                text=name,
                image=icon,
                compound="left",
                bootstyle="primary-outline",
                command=lambda n=name, pc=payment_class: self.select_method(n, pc)
            )
            button.grid(row=index // 3, column=index % 3, sticky="ew",
                        padx=3, pady=3, ipady=2)
            self.method_buttons[name] = button

        ttk.Label(details, text="Cash tendered", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=5)
        self.cash_entry = ttk.Entry(details)
        self.cash_entry.grid(row=3, column=1, sticky="ew", padx=(15, 0), pady=5)

        action_frame = ttk.Frame(details, style="Card.TFrame")
        action_frame.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(action_frame, text="Pay", bootstyle="success", width=10,
                   command=lambda: self.process_payment(self.selected["class"]())
                   ).pack(side="left", padx=(0, 10))
        ttk.Button(action_frame, text="Clear log", bootstyle="secondary-outline",
                   width=10, command=self.clear_log).pack(side="left")

    def _build_receipt_panel(self):
        receipt_box = ttk.Labelframe(self.card, text="Latest Receipt",
                                     style="Card.TLabelframe", padding=10)
        receipt_box.pack(fill="x", pady=(12, 0))

        qr_holder = ttk.Frame(receipt_box, style="Card.TFrame", width=120, height=120)
        qr_holder.pack(side="left", padx=(0, 15))
        qr_holder.pack_propagate(False)
        self.qr_label = ttk.Label(qr_holder, text="No QR yet", style="Card.TLabel",
                                  foreground="#9ca3af", anchor="center")
        self.qr_label.pack(expand=True)

        info = ttk.Frame(receipt_box, style="Card.TFrame")
        info.pack(side="left", fill="both", expand=True)
        self.receipt_label = ttk.Label(
            info, style="Card.TLabel", justify="left", wraplength=400,
            text="Make a successful payment to generate a QR code and receipt.")
        self.receipt_label.pack(anchor="w")
        self.save_button = ttk.Button(info, text="Save PDF receipt",
                                      bootstyle="secondary-outline",
                                      state="disabled", command=self.save_pdf)
        self.save_button.pack(anchor="w", pady=(10, 0))

    def _build_log(self):
        log_box = ttk.Labelframe(self.card, text="Transaction Log",
                                 style="Card.TLabelframe", padding=8)
        log_box.pack(fill="both", expand=True, pady=(12, 0))

        scroll = ttk.Scrollbar(log_box, orient="vertical")
        scroll.pack(side="right", fill="y")
        self.log_text = tk.Text(log_box, height=5, wrap="word", state="disabled",
                                relief="solid", borderwidth=1, font=("Consolas", 9),
                                yscrollcommand=scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll.configure(command=self.log_text.yview)

    # ------------------------------------------------------------ actions
    def select_method(self, name, payment_class):
        self.selected["name"] = name
        self.selected["class"] = payment_class
        for label, button in self.method_buttons.items():
            button.configure(bootstyle="primary" if label == name else "primary-outline")
        self.cash_entry.configure(state="normal" if name == "Cash" else "disabled")

    def add_log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def show_receipt(self, result):
        receipt = self.last_receipt
        qr_image = ImageTk.PhotoImage(make_qr(
            f"{self.business_name}\n{receipt['number']}\n{result}", 110))
        self.qr_label.configure(image=qr_image, text="")
        self.qr_label.image = qr_image

        lines = [f"Receipt No. {receipt['number']}", f"Payer: {receipt['payer']}", result]
        if receipt["tendered"] is not None:
            lines.append(f"Cash tendered: {php(receipt['tendered'])}   "
                         f"Change: {php(receipt['change'])}")
        self.receipt_label.configure(text="\n".join(lines))
        self.save_button.configure(state="normal")

    def process_payment(self, payment):
        try:
            amount = float(self.amount_entry.get())
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter a valid amount."
            )
            return
        if amount <= 0:
            messagebox.showerror(
                "Invalid Amount",
                "Please enter an amount greater than zero."
            )
            return

        tendered = change = None
        if self.selected["name"] == "Cash":
            try:
                tendered = float(self.cash_entry.get())
            except ValueError:
                messagebox.showerror(
                    "Invalid Input",
                    "Please enter the cash tendered."
                )
                return
            if tendered < amount:
                messagebox.showerror(
                    "Insufficient Payment",
                    f"Insufficient payment.\nPlease enter an amount equal to or greater than {php(amount)}."
                )
                return
            change = tendered - amount

        result = payment.pay(amount)
        self.history.append((payment.__class__.__name__, amount, result))
        log_payment(len(self.history), result)

        now = datetime.now()
        self.last_receipt.clear()
        self.last_receipt.update({
            "business": self.business_name,
            "number": f"{len(self.history):06d}",
            "date": now.strftime("%B %d, %Y"),
            "time": now.strftime("%I:%M %p"),
            "payer": self.name_entry.get().strip() or "Walk-in Customer",
            "method": self.selected["name"],
            "amount": amount,
            "tendered": tendered,
            "change": change,
            "result": result,
        })

        entry = (f"#{len(self.history)} [{self.last_receipt['time']}] "
                 f"{self.last_receipt['payer']}: {result}")
        if change is not None:
            entry += f" Change: {php(change)}"
        self.add_log(entry)
        self.show_receipt(result)

        for field in (self.name_entry, self.amount_entry, self.cash_entry):
            field.delete(0, "end")

    def save_pdf(self):
        if not self.last_receipt:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=f"receipt_{self.last_receipt['number']}.pdf",
            filetypes=[("PDF file", "*.pdf")]
        )
        if path:
            make_receipt_pdf(self.last_receipt, path)
            messagebox.showinfo("Saved", f"Receipt saved to {path}")

    def clear_log(self):
        if self.history and not messagebox.askyesno(
                "Clear log",
                "This also clears the payment history used by Chart and Export. Continue?"):
            return
        self.history.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def export(self):
        if not self.history:
            messagebox.showinfo("Nothing to Export", "Make a payment first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV file", "*.csv")]
        )
        if path:
            export_csv(self.history, path)
            messagebox.showinfo("Exported", f"Saved to {path}")

    def exit_app(self):
        show_history(self.history)
        self.window.destroy()