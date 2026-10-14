import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from PIL import ImageTk

from restaurant.payment_methods import METHODS
from ui import theme
from utils.icons import make_icon
from utils.formatting import php


class PaymentDialog(tk.Toplevel):
    """Asks the cashier for a payment method and its details.

    The dialog builds a payment object from the chosen method and hands it to
    on_confirm(payment, spec, info). Every method is handled the same way.
    """

    def __init__(self, parent, total, on_confirm, note=""):
        super().__init__(parent)
        self.title("Payment")
        self.resizable(False, False)
        self.transient(parent)
        self.configure(background=theme.CARD)

        self.total = total
        self.note = note
        self.on_confirm = on_confirm
        self.spec = None
        self.icons = []
        self.buttons = {}

        self._build()
        self.bind("<Return>", lambda event: self.confirm())
        self.bind("<Escape>", lambda event: self.destroy())

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()

    def _build(self):
        body = ttk.Frame(self, style="Card.TFrame", padding=24)
        body.pack(fill="both", expand=True)

        due = ttk.Frame(body, style="Stat.TFrame", padding=(16, 12))
        due.pack(fill="x", pady=(0, 16))
        ttk.Label(due, text="TOTAL AMOUNT", style="StatMuted.TLabel").pack()
        ttk.Label(due, text=php(self.total), style="Stat.TLabel", foreground=theme.GREEN,
                  font=(theme.FONT, 26, "bold")).pack()
        if self.note:
            ttk.Label(due, text=self.note, style="StatMuted.TLabel").pack()

        ttk.Label(body, text="Select a payment method", style="Title.TLabel").pack(anchor="w")
        grid = ttk.Frame(body, style="Card.TFrame")
        grid.pack(fill="x", pady=(6, 12))
        for column in range(3):
            grid.columnconfigure(column, weight=1, uniform="method")
        for index, spec in enumerate(METHODS):
            icon = ImageTk.PhotoImage(make_icon(spec.name))
            self.icons.append(icon)
            button = ttk.Button(grid, text=spec.name, image=icon, compound="left",
                                style="Chip.TButton",
                                command=lambda s=spec: self.select_method(s))
            button.grid(row=index // 3, column=index % 3, sticky="ew",
                        padx=3, pady=3, ipady=4)
            self.buttons[spec.name] = button

        self.field_label = ttk.Label(body, text="Payment details", style="Title.TLabel")
        self.field_label.pack(anchor="w")
        self.entry = ttk.Entry(body, width=34, state="disabled", font=(theme.FONT, 12))
        self.entry.pack(fill="x", pady=(6, 4), ipady=4)
        self.hint_label = ttk.Label(body, text="Choose a payment method first.",
                                    style="Muted.TLabel")
        self.hint_label.pack(anchor="w")

        actions = ttk.Frame(body, style="Card.TFrame")
        actions.pack(fill="x", pady=(20, 0))
        ttk.Button(actions, text="CONFIRM PAYMENT", style="Go.TButton",
                   command=self.confirm).pack(side="left", expand=True, fill="x", padx=(0, 8))
        ttk.Button(actions, text="Cancel", style="Ghost.TButton",
                   command=self.destroy).pack(side="left", ipady=6)

    def select_method(self, spec):
        self.spec = spec
        for name, button in self.buttons.items():
            button.configure(style="ChipOn.TButton" if name == spec.name else "Chip.TButton")
        self.field_label.configure(text=spec.field_label)
        self.hint_label.configure(text=spec.hint)
        self.entry.configure(state="normal")
        self.entry.delete(0, "end")
        self.entry.focus_set()

    def confirm(self):
        if self.spec is None:
            messagebox.showerror("No Payment Method",
                                 "Please select a payment method.", parent=self)
            return
        try:
            info = self.spec.validate(self.entry.get(), self.total)
        except ValueError as error:
            message = str(error)
            title = "Insufficient Payment" if message.startswith("Insufficient") else "Invalid Input"
            messagebox.showerror(title, message, parent=self)
            return
        payment = self.spec.payment_class()
        if self.on_confirm(payment, self.spec, info):
            self.destroy()
