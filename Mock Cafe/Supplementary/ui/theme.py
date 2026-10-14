"""Colours and ttk styles shared by every window, so the app looks the same everywhere."""


ESPRESSO = "#2b1b12"
ROAST = "#6b4226"
CARAMEL = "#c8863f"
CARAMEL_DARK = "#a96d2c"
CREAM = "#f6efe4"
CARD = "#ffffff"
LINE = "#e6d9c6"
INK = "#2b1b12"
MUTED = "#8a7a6c"
GREEN = "#2f8f5b"
GREEN_DARK = "#26774c"
RED = "#c0392b"

FONT = "Segoe UI"


def _button(style, name, bg, fg, hover, border=None, font=(FONT, 10, "bold"),
            padding=(14, 8)):
    style.configure(name, background=bg, foreground=fg, bordercolor=border or bg,
                    lightcolor=bg, darkcolor=bg, focuscolor=bg, relief="flat",
                    borderwidth=1, font=font, padding=padding, anchor="center")
    style.map(name, background=[("pressed", hover), ("active", hover)],
              bordercolor=[("active", border or hover)],
              lightcolor=[("active", hover)], darkcolor=[("active", hover)])


def apply_styles(style):
    # frames and labels
    style.configure("Header.TFrame", background=ESPRESSO)
    style.configure("Header.TLabel", background=ESPRESSO, foreground="white")
    style.configure("Cream.TFrame", background=CREAM)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card.TLabel", background=CARD, foreground=INK, font=(FONT, 10))
    style.configure("Muted.TLabel", background=CARD, foreground=MUTED, font=(FONT, 9))
    style.configure("Title.TLabel", background=CARD, foreground=INK, font=(FONT, 11, "bold"))
    style.configure("Panel.TLabelframe", background=CARD, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, relief="solid", borderwidth=1)
    style.configure("Panel.TLabelframe.Label", background=CARD, foreground=ROAST,
                    font=(FONT, 10, "bold"))
    style.configure("Stat.TFrame", background=CREAM)
    style.configure("Stat.TLabel", background=CREAM, foreground=INK, font=(FONT, 10))
    style.configure("StatMuted.TLabel", background=CREAM, foreground=MUTED, font=(FONT, 9))

    # buttons
    _button(style, "Accent.TButton", CARAMEL, "white", CARAMEL_DARK)
    _button(style, "Chip.TButton", CREAM, ROAST, "#efe2cc", border=LINE,
            font=(FONT, 10, "bold"), padding=(16, 8))
    _button(style, "ChipOn.TButton", ESPRESSO, "white", ROAST,
            font=(FONT, 10, "bold"), padding=(16, 8))
    _button(style, "Accent.TButton", CARAMEL, "white", CARAMEL_DARK)
    _button(style, "Go.TButton", GREEN, "white", GREEN_DARK,
            font=(FONT, 10, "bold"), padding=(8, 12))
    _button(style, "Ghost.TButton", "#f6efe4", ROAST, "#eadfce", border=LINE)
    _button(style, "Danger.TButton", "#fbe9e6", RED, "#f6d4cf", border="#efc3bd")
    _button(style, "Small.TButton", "#f6efe4", ROAST, "#eadfce", border=LINE,
            font=(FONT, 12, "bold"), padding=(8, 2))

    # order table
    style.configure("Treeview", rowheight=36, font=(FONT, 10), background=CARD,
                    fieldbackground=CARD, foreground=INK, borderwidth=0)
    style.configure("Treeview.Heading", font=(FONT, 9, "bold"), background=CREAM,
                    foreground=ROAST, relief="flat", padding=(6, 8))
    style.map("Treeview", background=[("selected", "#f3dcb8")],
              foreground=[("selected", INK)])
