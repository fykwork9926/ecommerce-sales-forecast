"""Limpeza dos dados e detecção de anomalias.

O dataset tem vários "problemas" reais que precisam ser tratados antes de
qualquer análise: quantidades negativas, cancelamentos, preços zerados,
linhas duplicadas, códigos que não são produtos e pedidos gigantes que
foram cancelados logo depois.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from salesforecast.config import PRODUCT_CODE_PATTERN


@dataclass
class AnomalyReport:
    """Contagem de cada tipo de anomalia encontrada."""

    total_rows: int = 0
    invalid_rows: int = 0
    duplicates: int = 0
    cancellations: int = 0
    cancelled_value: float = 0.0
    negative_adjustments: int = 0
    non_positive_price: int = 0
    non_product_codes: int = 0
    matched_cancelled_sales: int = 0
    missing_customer: int = 0
    quantity_outliers: int = 0
    clean_rows: int = 0

    def as_rows(self) -> list[tuple[str, int | float]]:
        """Lista (descrição, valor) usada no relatório e na exportação."""
        return [
            ("Linhas no arquivo", self.total_rows),
            ("Linhas inválidas (data/número)", self.invalid_rows),
            ("Linhas duplicadas", self.duplicates),
            ("Cancelamentos (nota 'C...')", self.cancellations),
            ("Valor cancelado (£)", self.cancelled_value),
            ("Qtd. negativa sem cancelamento", self.negative_adjustments),
            ("Preço zero ou negativo", self.non_positive_price),
            ("Códigos que não são produto", self.non_product_codes),
            ("Vendas anuladas por cancelamento", self.matched_cancelled_sales),
            ("Vendas sem cliente identificado", self.missing_customer),
            ("Quantidades fora do padrão", self.quantity_outliers),
            ("Linhas válidas após limpeza", self.clean_rows),
        ]


@dataclass
class CleanResult:
    """Dados limpos + cancelamentos + relatório de anomalias."""

    sales: pd.DataFrame
    cancellations: pd.DataFrame
    report: AnomalyReport


def _remove_matched_cancellations(
    sales: pd.DataFrame, cancellations: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    """Remove vendas que foram integralmente canceladas depois.

    Ex.: o cliente comprou 80.995 unidades e a mesma quantidade foi
    cancelada minutos depois. Sem isso, o pedido inflaria as análises.
    Cada cancelamento anula no máximo uma venda com mesmo cliente,
    produto e quantidade.
    """
    keys = ["CustomerID", "StockCode", "Quantity"]
    cancelled = cancellations.dropna(subset=["CustomerID"]).copy()
    if cancelled.empty:
        return sales, 0
    cancelled["Quantity"] = -cancelled["Quantity"]
    counts = cancelled.groupby(keys).size().rename("n_cancel")

    result = sales.copy()
    # Numera as vendas repetidas (0, 1, 2...) dentro de cada combinação.
    result["_order"] = result.groupby(keys, dropna=False).cumcount()
    result = result.join(counts, on=keys)
    to_drop = result["n_cancel"].fillna(0) > result["_order"]
    result = result.loc[~to_drop].drop(columns=["_order", "n_cancel"])
    return result, int(to_drop.sum())


def clean_transactions(df: pd.DataFrame,
                       outlier_factor: float = 3.0) -> CleanResult:
    """Aplica todas as regras de limpeza e devolve o resultado."""
    if outlier_factor <= 0:
        raise ValueError("outlier_factor deve ser maior que zero.")

    report = AnomalyReport(total_rows=len(df))
    data = df.copy()
    data["InvoiceNo"] = data["InvoiceNo"].astype(str).str.strip()
    data["StockCode"] = data["StockCode"].astype(str).str.strip().str.upper()
    data["Description"] = data["Description"].fillna("").str.strip()

    # 1) Linhas sem data, quantidade ou preço válidos.
    invalid = data[["InvoiceDate", "Quantity", "UnitPrice"]].isna()
    invalid = invalid.any(axis=1)
    report.invalid_rows = int(invalid.sum())
    data = data.loc[~invalid].copy()
    data["Quantity"] = data["Quantity"].round().astype("int64")

    # 2) Duplicatas exatas.
    duplicated = data.duplicated()
    report.duplicates = int(duplicated.sum())
    data = data.loc[~duplicated]

    # 3) Cancelamentos: notas que começam com "C".
    is_cancel = data["InvoiceNo"].str.startswith("C")
    cancellations = data.loc[is_cancel].copy()
    report.cancellations = len(cancellations)
    report.cancelled_value = round(float(
        -(cancellations["Quantity"] * cancellations["UnitPrice"]).sum()
    ), 2)
    sales = data.loc[~is_cancel]

    # 4) Quantidade negativa/zero sem nota de cancelamento (ajuste de estoque).
    negative = sales["Quantity"] <= 0
    report.negative_adjustments = int(negative.sum())
    sales = sales.loc[~negative]

    # 5) Preço zero ou negativo (brindes, ajustes contábeis).
    bad_price = sales["UnitPrice"] <= 0
    report.non_positive_price = int(bad_price.sum())
    sales = sales.loc[~bad_price]

    # 6) Códigos que não são produtos (frete, taxas, manuais).
    is_product = sales["StockCode"].str.match(PRODUCT_CODE_PATTERN)
    report.non_product_codes = int((~is_product).sum())
    sales = sales.loc[is_product]

    # 7) Vendas anuladas por um cancelamento correspondente.
    sales, report.matched_cancelled_sales = _remove_matched_cancellations(
        sales, cancellations
    )

    # 8) Outliers de quantidade: regra do IQR na escala logarítmica.
    # Apenas marcamos (coluna IsOutlier); compras no atacado são legítimas.
    log_qty = np.log1p(sales["Quantity"].to_numpy(dtype=float))
    q1, q3 = np.percentile(log_qty, [25, 75]) if len(log_qty) else (0, 0)
    upper = q3 + outlier_factor * (q3 - q1)
    sales = sales.assign(IsOutlier=log_qty > upper)
    report.quantity_outliers = int(sales["IsOutlier"].sum())

    report.missing_customer = int(sales["CustomerID"].isna().sum())
    sales = sales.assign(Revenue=sales["Quantity"] * sales["UnitPrice"])
    sales = sales.sort_values("InvoiceDate").reset_index(drop=True)
    report.clean_rows = len(sales)
    return CleanResult(sales, cancellations, report)
