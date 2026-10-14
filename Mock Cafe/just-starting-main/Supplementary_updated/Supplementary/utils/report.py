import tkinter as tk
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from utils.formatting import php

# Same colours as the payment icons so each method looks the same everywhere.
METHOD_STYLE = {
    "CashPayment": ("Cash", "#2ecc71"),
    "EWalletPayment": ("E-Wallet", "#0d6efd"),
    "CreditCardPayment": ("Credit Card", "#f1c40f"),
    "DebitCardPayment": ("Debit Card", "#e67e22"),
    "BankTransferPayment": ("Bank Transfer", "#34495e"),
}

INK = "#2b1b12"
MUTED = "#8a7a6c"
CREAM = "#fbf6ee"
GRID = "#eadfce"


def to_dataframe(history):
    return pd.DataFrame(history, columns=["Method", "Amount (PHP)", "Result"])


def export_csv(history, path):
    to_dataframe(history).to_csv(path, index=False, encoding="utf-8-sig")


def summarize(history):
    """Per-method totals: a list of (label, colour, count, sales)."""
    data = to_dataframe(history)
    rows = []
    for key, (label, colour) in METHOD_STYLE.items():
        part = data[data["Method"] == key]
        if len(part):
            rows.append((label, colour, len(part), float(part["Amount (PHP)"].sum())))
    return rows


def _clean(axes):
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(GRID)
    axes.set_facecolor(CREAM)
    axes.tick_params(colors=MUTED, length=0, labelsize=9)


def draw_charts(figure, history):
    figure.clear()
    figure.set_facecolor(CREAM)

    if not history:
        figure.text(0.5, 0.54, "No payments yet", ha="center", va="center",
                    fontsize=18, fontweight="bold", color=INK)
        figure.text(0.5, 0.44, "Complete a transaction and the charts will appear here.",
                    ha="center", va="center", fontsize=10, color=MUTED)
        return

    rows = summarize(history)
    labels = [r[0] for r in rows]
    colours = [r[1] for r in rows]
    counts = [r[2] for r in rows]
    sales = [r[3] for r in rows]

    grid = figure.add_gridspec(1, 2, width_ratios=[1.25, 1], left=0.07, right=0.97,
                               top=0.74, bottom=0.17, wspace=0.28)

    # ---- bar chart: how many payments per method
    bars_ax = figure.add_subplot(grid[0])
    _clean(bars_ax)
    bars = bars_ax.bar([l.replace(" ", "\n") for l in labels], counts, color=colours, width=0.58, zorder=3)
    bars_ax.bar_label(bars, padding=4, fontsize=10, fontweight="bold", color=INK)
    bars_ax.set_ylim(0, max(counts) * 1.25)
    bars_ax.set_yticks(range(0, int(max(counts) * 1.25) + 2))
    bars_ax.yaxis.grid(True, color=GRID, zorder=0)
    bars_ax.set_axisbelow(True)
    bars_ax.set_title("Payments per method", loc="left", fontsize=11,
                      fontweight="bold", color=INK, pad=12)

    # ---- donut chart: share of sales per method
    donut_ax = figure.add_subplot(grid[1])
    donut_ax.set_facecolor(CREAM)
    donut_ax.pie(sales, colors=colours, startangle=90, counterclock=False,
                 wedgeprops=dict(width=0.38, edgecolor=CREAM, linewidth=2))
    donut_ax.text(0, 0.08, php(sum(sales)), ha="center", va="center",
                  fontsize=12, fontweight="bold", color=INK)
    donut_ax.text(0, -0.17, "total sales", ha="center", va="center",
                  fontsize=8, color=MUTED)
    donut_ax.set_title("Share of sales", loc="left", fontsize=11,
                       fontweight="bold", color=INK, pad=12)
    donut_ax.legend(labels, loc="upper center", bbox_to_anchor=(0.5, 0.02),
                    ncol=2, frameon=False, fontsize=8, labelcolor=MUTED,
                    handlelength=1, columnspacing=1.2)

    figure.text(0.07, 0.93, "Sales Report", fontsize=15, fontweight="bold", color=INK)
    figure.text(0.07, 0.875,
                f"{sum(counts)} transactions   |   Average sale {php(sum(sales) / sum(counts))}"
                "   |   VAT included",
                fontsize=9, color=MUTED)


def show_chart(parent, history, logo=None):
    window = tk.Toplevel(parent)
    window.title("Sales Report")
    window.configure(background=CREAM)
    if logo is not None:
        window.iconphoto(False, logo)

    figure = Figure(figsize=(9.2, 4.6), dpi=100)
    draw_charts(figure, history)

    canvas = FigureCanvasTkAgg(figure, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
