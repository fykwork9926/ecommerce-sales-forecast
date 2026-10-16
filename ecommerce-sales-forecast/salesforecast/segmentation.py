"""Segmentação de clientes pelo modelo RFM.

R (Recência): há quantos dias o cliente comprou pela última vez.
F (Frequência): quantos pedidos diferentes ele fez.
M (Valor monetário): quanto ele gastou no total.
Cada dimensão recebe uma nota de 1 a 5 (quintis) e a combinação das
notas define o segmento.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _quintile_score(values: pd.Series, higher_is_better: bool) -> pd.Series:
    """Converte valores em notas de 1 a 5 usando quintis.

    O rank com method="first" desempata valores iguais, evitando que o
    qcut falhe quando muitos clientes têm, por exemplo, 1 pedido só.
    """
    bins = min(5, len(values))
    ranks = values.rank(method="first", ascending=higher_is_better)
    scores = pd.qcut(ranks, bins, labels=range(1, bins + 1)).astype(int)
    return scores


def rfm_table(sales: pd.DataFrame,
              snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    """Calcula as métricas e o segmento RFM de cada cliente."""
    data = sales.dropna(subset=["CustomerID"])
    if data.empty:
        raise ValueError("nenhuma venda com cliente identificado.")
    if snapshot is None:
        snapshot = data["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

    rfm = data.groupby("CustomerID").agg(
        LastPurchase=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Revenue", "sum"),
    )
    rfm["Recency"] = (snapshot - rfm["LastPurchase"]).dt.days
    rfm["R"] = _quintile_score(rfm["Recency"], higher_is_better=False)
    rfm["F"] = _quintile_score(rfm["Frequency"], higher_is_better=True)
    rfm["M"] = _quintile_score(rfm["Monetary"], higher_is_better=True)

    r, fm = rfm["R"], (rfm["F"] + rfm["M"]) / 2
    conditions = [
        (r >= 4) & (fm >= 4),
        (r >= 3) & (fm >= 3),
        r >= 4,
        (r <= 2) & (fm >= 3),
        r == 3,
    ]
    segments = ["Campeões", "Clientes fiéis", "Promissores",
                "Em risco", "Precisam de atenção"]
    rfm["Segment"] = np.select(conditions, segments, default="Hibernando")
    rfm["Monetary"] = rfm["Monetary"].round(2)
    return rfm[["Recency", "Frequency", "Monetary", "R", "F", "M",
                "Segment"]]


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Tamanho e comportamento médio de cada segmento."""
    summary = rfm.groupby("Segment").agg(
        Customers=("Recency", "size"),
        AvgRecency=("Recency", "mean"),
        AvgFrequency=("Frequency", "mean"),
        AvgMonetary=("Monetary", "mean"),
        Revenue=("Monetary", "sum"),
    )
    summary = summary.round(2)
    # Participações ficam com 4 casas (ex.: 0.2215 = 22,15%).
    summary["CustomerShare"] = (summary["Customers"] / len(rfm)).round(4)
    summary["RevenueShare"] = (
        summary["Revenue"] / rfm["Monetary"].sum()
    ).round(4)
    return summary.sort_values("Revenue", ascending=False)
