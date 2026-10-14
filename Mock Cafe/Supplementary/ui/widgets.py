import tkinter as tk

from ui import theme

TILE = "#fbf6ee"
TILE_HOVER = "#fff0d6"


class MenuCard(tk.Frame):
    """A big clickable menu tile showing an item's picture (optional), name and price."""

    def __init__(self, parent, name, price_text, command, image=None):
        super().__init__(parent, bg=TILE, highlightbackground=theme.LINE,
                         highlightthickness=1, cursor="hand2")
        self.command = command
        self.selected = False
        self.image = image                       # keep a reference so Tk does not drop it

        self.image_label = None
        if image is not None:
            self.image_label = tk.Label(self, image=image, bg=TILE, cursor="hand2")
            self.image_label.pack(pady=(8, 0))

        self.name_label = tk.Label(self, text=name, bg=TILE, fg=theme.INK, cursor="hand2",
                                   font=(theme.FONT, 12, "bold"), wraplength=190)
        self.price_label = tk.Label(self, text=price_text, bg=TILE, fg=theme.CARAMEL_DARK,
                                    cursor="hand2", font=(theme.FONT, 11, "bold"))
        top = 2 if image is not None else 14
        self.name_label.pack(expand=True, fill="x", padx=8, pady=(top, 0))
        self.price_label.pack(expand=True, fill="x", padx=8, pady=(0, 8))

        for widget in (self, self.name_label, self.price_label, self.image_label):
            if widget is None:
                continue
            widget.bind("<Button-1>", lambda event: self.command())
            widget.bind("<Enter>", lambda event: self._paint(hover=True))
            widget.bind("<Leave>", lambda event: self._paint())

    def set_selected(self, selected):
        self.selected = selected
        self._paint()

    def _paint(self, hover=False):
        if self.selected:
            bg, name, price, border = theme.CARAMEL, "white", "white", theme.CARAMEL_DARK
        else:
            bg = TILE_HOVER if hover else TILE
            name, price, border = theme.INK, theme.CARAMEL_DARK, theme.LINE
        self.configure(bg=bg, highlightbackground=border)
        self.name_label.configure(bg=bg, fg=name)
        self.price_label.configure(bg=bg, fg=price)
        if self.image_label is not None:
            self.image_label.configure(bg=bg)