import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from PIL import ImageTk

from ui import theme
from utils.qr import make_qr
from utils.receipt import make_pos_receipt_pdf


class ReceiptWindow(tk.Toplevel):
    """Shows the receipt text and QR code. Closing it starts a new transaction."""

    def __init__(self, parent, receipt, result, on_new_transaction, logo=None):
        super().__init__(parent)
        self.title(f"Receipt {receipt.number_text}")
        self.resizable(False, False)
        self.transient(parent)
        self.configure(background=theme.CARD)

        self.receipt = receipt
        self.on_new_transaction = on_new_transaction

        body = ttk.Frame(self, style="Card.TFrame", padding=22)
        body.pack(fill="both", expand=True)

        if logo is not None:
            self.logo = logo
            self.iconphoto(False, logo)
        ttk.Label(body, text="PAYMENT SUCCESSFUL", style="Card.TLabel", foreground=theme.GREEN,
                  font=(theme.FONT, 16, "bold")).pack()
        ttk.Label(body, text=result, style="Muted.TLabel").pack(pady=(2, 14))

        middle = ttk.Frame(body, style="Card.TFrame")
        middle.pack()

        lines = receipt.lines()
        text = tk.Text(middle, width=max(len(line) for line in lines) + 2,
                       height=len(lines) + 1, font=("Consolas", 10), relief="flat",
                       borderwidth=0, wrap="none", background=theme.CREAM,
                       foreground=theme.INK, padx=14, pady=12)
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")
        text.pack(side="left")

        side = ttk.Frame(middle, style="Card.TFrame")
        side.pack(side="left", padx=(20, 0), anchor="n")
        self.qr_image = ImageTk.PhotoImage(make_qr(receipt.qr_payload, 160))
        ttk.Label(side, image=self.qr_image, style="Card.TLabel").pack()
        ttk.Label(side, text="Scan for your receipt", style="Muted.TLabel").pack(pady=(4, 18))
        ttk.Button(side, text="Save PDF Receipt", style="Ghost.TButton",
                   command=self.save_pdf).pack(fill="x", pady=4)
        ttk.Button(side, text="NEW TRANSACTION", style="Go.TButton",
                   command=self.new_transaction).pack(fill="x", pady=4)

        self.protocol("WM_DELETE_WINDOW", self.new_transaction)

        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_reqwidth()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_reqheight()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.wait_visibility()
        self.grab_set()

    def save_pdf(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".pdf",
            initialfile=f"receipt_{self.receipt.number_text}.pdf",
            filetypes=[("PDF file", "*.pdf")]
        )
        if not path:
            return
        try:
            make_pos_receipt_pdf(self.receipt.lines(peso=False), self.receipt.qr_payload, path)
        except OSError as error:
            messagebox.showerror("Could Not Save", str(error), parent=self)
            return
        messagebox.showinfo("Saved", f"Receipt saved to {path}", parent=self)

    def new_transaction(self):
        self.grab_release()
        self.destroy()
        self.on_new_transaction()
