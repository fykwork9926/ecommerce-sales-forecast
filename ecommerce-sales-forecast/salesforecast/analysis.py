"""Análises descritivas: séries temporais, países e produtos."""

from __future__ import annotations

import pandas as pd


def monthly_summary(sales: pd.DataFrame) -> pd.DataFrame:
    """Receita, pedidos e clientes por mês."""
    month = sales["InvoiceDate"].dt.to_period("M")
    summary = sales.groupby(month).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
    )
    summary.index = summary.index.astype(str)
    summary.index.name = "Month"
    summary["Revenue"] = summary["Revenue"].round(2)
    return summary


def weekly_revenue(sales: pd.DataFrame,
                   drop_incomplete: bool = True) -> pd.Series:
    """Receita semanal (segunda a domingo), base da previsão.

    Semanas incompletas no início e no fim do período distorcem a série
    (ex.: os dados terminam numa sexta-feira), então são removidas.
    """
    if sales.empty:
        raise ValueError("não há vendas para montar a série semanal.")

    series = (sales.set_index("InvoiceDate")["Revenue"]
              .resample("W-MON", label="left", closed="left").sum())
    if drop_incomplete and len(series) > 2:
        first_day = sales["InvoiceDate"].min().normalize()
        last_day = sales["InvoiceDate"].max().normalize()
        if first_day > series.index[0]:
            series = series.iloc[1:]
        if (last_day - series.index[-1]).days < 6:
            series = series.iloc[:-1]
    series.name = "Revenue"
    series.index.name = "WeekStart"
    return series.round(2)


def country_summary(sales: pd.DataFrame,
                    min_orders: int = 10) -> pd.DataFrame:
    """Compara o tamanho médio dos pedidos entre países."""
    if min_orders < 1:
        raise ValueError("min_orders deve ser maior que zero.")

    grouped = sales.groupby("Country").agg(
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
        Items=("Quantity", "sum"),
        Revenue=("Revenue", "sum"),
    )
    grouped = grouped[grouped["Orders"] >= min_orders].copy()
    grouped["AvgOrderValue"] = grouped["Revenue"] / grouped["Orders"]
    grouped["AvgItemsPerOrder"] = grouped["Items"] / grouped["Orders"]
    share = grouped["Revenue"] / sales["Revenue"].sum()
    grouped = grouped.round(2)
    grouped["RevenueShare"] = share.round(4)
    return grouped.sort_values("AvgOrderValue", ascending=False)
