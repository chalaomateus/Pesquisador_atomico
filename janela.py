import tkinter as tk
from datetime import datetime

import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

VS_CURRENCY = "usd"
DAYS = "1"
REFRESH_MS = 60_000
API_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"


def fetch_prices(days: str):
    params = {"vs_currency": VS_CURRENCY, "days": days}
    if days == "max":
        params["interval"] = "daily"

    r = requests.get(API_URL, params=params, timeout=20)
    r.raise_for_status()
    prices = r.json()["prices"]

    xs = [datetime.fromtimestamp(ts / 1000) for ts, _ in prices]
    ys = [price for _, price in prices]
    return xs, ys


def redraw():
    xs, ys = fetch_prices(DAYS)
    ax.clear()
    ax.plot(xs, ys)
    titulo = "Bitcoin (Hoje)" if DAYS == "1" else "Bitcoin (Histórico total)"
    ax.set_title(f"{titulo} — {VS_CURRENCY.upper()}")
    ax.set_ylabel("Preço")
    fig.autofmt_xdate()
    canvas.draw()


def tick():
    try:
        redraw()
    finally:
        root.after(REFRESH_MS, tick)


root = tk.Tk()
root.title("BTC Gráfico")

fig = Figure(figsize=(9, 5), dpi=100)
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill="both", expand=True)

redraw()
root.after(REFRESH_MS, tick)
root.mainloop()

