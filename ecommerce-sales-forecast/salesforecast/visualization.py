"""Gráficos salvos em PNG com Matplotlib."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera imagens sem precisar de janela/tela
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

from salesforecast.forecasting import ForecastResult  # noqa: E402

# Paleta: azul para dados reais, laranja para previsões.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e4e3df"


def _pounds(value: float, _position: int = 0) -> str:
    """Formata eixos em libras: 12000 -> £12k."""
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"£{value / 1_000:.0f}k"
    return f"£{value:.0f}"


def _style(ax: plt.Axes, title: str) -> None:
    """Visual limpo: sem bordas superiores/direitas e grade discreta."""
    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=12,
                 fontweight="bold")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.set_axisbelow(True)


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)
    return path


def plot_monthly_revenue(monthly: pd.DataFrame, path: Path) -> Path:
    """Barras com a receita de cada mês."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(monthly.index, monthly["Revenue"], color=BLUE, width=0.7)
    ax.yaxis.set_major_formatter(FuncFormatter(_pounds))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(axis="x", rotation=45)
    _style(ax, "Receita mensal")
    return _save(fig, path)


def plot_forecast(result: ForecastResult, path: Path) -> Path:
    """Histórico semanal, backtest e previsão com intervalo."""
    fig, ax = plt.subplots(figsize=(11, 5))
    history, forecast = result.history, result.forecast

    ax.plot(history.index, history.values, color=BLUE, linewidth=2,
            label="Receita real")
    ax.plot(result.backtest.index, result.backtest.values, color=ORANGE,
            linewidth=2, linestyle=":", label="Backtest (teste)")
    ax.plot(forecast.index, forecast["Forecast"], color=ORANGE, linewidth=2,
            marker="o", markersize=5, label="Previsão")
    ax.fill_between(forecast.index, forecast["Lower"], forecast["Upper"],
                    color=ORANGE, alpha=0.15, linewidth=0,
                    label="Intervalo aproximado (95%)")
    ax.axvline(result.backtest.index[0], color=MUTED, linewidth=0.8,
               linestyle="--")
    ax.yaxis.set_major_formatter(FuncFormatter(_pounds))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    _style(ax, f"Receita semanal e previsão — modelo: {result.best_model}")
    return _save(fig, path)


def plot_horizontal_bars(values: pd.Series, title: str, path: Path,
                         money: bool = True) -> Path:
    """Ranking em barras horizontais (maior valor no topo)."""
    ordered = values.sort_values()
    fig, ax = plt.subplots(figsize=(9, max(3.0, 0.42 * len(ordered) + 1)))
    ax.barh(ordered.index.astype(str), ordered.values, color=BLUE,
            height=0.65)
    formatter = _pounds if money else (lambda v, _p=0: f"{v:,.0f}")
    for y, value in enumerate(ordered.values):
        ax.text(value, y, " " + formatter(value), va="center",
                fontsize=8, color=MUTED)
    ax.xaxis.set_major_formatter(FuncFormatter(formatter))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.margins(x=0.12)
    _style(ax, title)
    return _save(fig, path)
