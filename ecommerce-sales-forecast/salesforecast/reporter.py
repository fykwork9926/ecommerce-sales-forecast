"""Relatório no terminal e exportação dos resultados em CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from salesforecast.cleaning import AnomalyReport
from salesforecast.forecasting import ForecastResult

WIDTH = 66


class ReportError(Exception):
    """Erro levantado quando não é possível salvar os resultados."""


def money(value: float) -> str:
    """Formata valores em libras esterlinas (moeda do dataset)."""
    return f"£{value:,.2f}"


def _section(title: str) -> None:
    print()
    print(f"▶ {title}")


def _row(label: str, value: object) -> None:
    print(f"  {label:.<36} {value}")


def print_report(report: AnomalyReport, monthly: pd.DataFrame,
                 countries: pd.DataFrame, segments: pd.DataFrame,
                 categories: pd.DataFrame, products: pd.DataFrame,
                 result: ForecastResult, top: int = 5) -> None:
    """Imprime o resumo de todas as análises."""
    print("═" * WIDTH)
    print("  SalesForecast — Análise e Previsão de Vendas")
    print("═" * WIDTH)

    _section("QUALIDADE DOS DADOS E ANOMALIAS")
    for label, value in report.as_rows():
        shown = money(value) if isinstance(value, float) else f"{value:,}"
        _row(label + " ", shown)

    _section("VISÃO GERAL")
    _row("Período ", f"{monthly.index[0]} a {monthly.index[-1]}")
    _row("Receita total ", money(monthly["Revenue"].sum()))
    _row("Produtos diferentes ", f"{len(products):,}")
    best_month = monthly["Revenue"].idxmax()
    _row("Melhor mês ", f"{best_month} "
         f"({money(monthly.loc[best_month, 'Revenue'])})")

    _section(f"TOP {top} PAÍSES POR TICKET MÉDIO (mín. 10 pedidos)")
    print(f"  {'País':<22}{'Pedidos':>9}{'Ticket médio':>15}"
          f"{'Itens/pedido':>14}")
    for country, row in countries.head(top).iterrows():
        print(f"  {country[:21]:<22}{int(row['Orders']):>9,}"
              f"{money(row['AvgOrderValue']):>15}"
              f"{row['AvgItemsPerOrder']:>14,.0f}")

    _section("SEGMENTOS DE CLIENTES (RFM)")
    print(f"  {'Segmento':<22}{'Clientes':>10}{'% clientes':>12}"
          f"{'% receita':>11}")
    for segment, row in segments.iterrows():
        print(f"  {segment:<22}{int(row['Customers']):>10,}"
              f"{row['CustomerShare']:>12.1%}{row['RevenueShare']:>11.1%}")

    _section("CATEGORIAS DE PRODUTOS")
    print(f"  {'Categoria':<22}{'Produtos':>10}{'Receita':>16}"
          f"{'% receita':>11}")
    for category, row in categories.iterrows():
        print(f"  {category:<22}{int(row['Products']):>10,}"
              f"{money(row['Revenue']):>16}{row['RevenueShare']:>11.1%}")
    abc = products["ABC"].value_counts().reindex(["A", "B", "C"]).fillna(0)
    print(f"  Curva ABC: A={int(abc['A'])} · B={int(abc['B'])} · "
          f"C={int(abc['C'])} produtos")

    _section("BACKTEST DOS MODELOS (últimas semanas escondidas)")
    print(f"  {'Modelo':<32}{'MAE':>14}{'MAPE':>10}")
    for score in result.scores:
        mark = " ◀ melhor" if score.name == result.best_model else ""
        print(f"  {score.name:<32}{money(score.mae):>14}"
              f"{score.mape:>9.1f}%{mark}")

    _section(f"PREVISÃO — PRÓXIMAS {len(result.forecast)} SEMANAS")
    for week, row in result.forecast.iterrows():
        print(f"  Semana de {week:%d/%m/%Y}  {money(row['Forecast']):>14}"
              f"   (entre {money(row['Lower'])} e {money(row['Upper'])})")
    print()
    print("═" * WIDTH)


def export_tables(output_dir: Path,
                  tables: dict[str, pd.DataFrame]) -> list[Path]:
    """Salva cada tabela como CSV (utf-8-sig para o Excel ler acentos)."""
    saved = []
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        for name, table in tables.items():
            path = output_dir / f"{name}.csv"
            table.to_csv(path, encoding="utf-8-sig")
            saved.append(path)
    except OSError as exc:
        raise ReportError(f"não foi possível salvar em {output_dir}: {exc}"
                          ) from exc
    return saved
