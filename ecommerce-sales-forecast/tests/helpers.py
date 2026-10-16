"""Dados sintéticos pequenos usados pelos testes."""

import pandas as pd


def make_raw(rows: list[tuple]) -> pd.DataFrame:
    """Cria um DataFrame no formato do dataset a partir de tuplas.

    Ordem: (InvoiceNo, StockCode, Description, Quantity, data,
            UnitPrice, CustomerID, Country)
    """
    df = pd.DataFrame(rows, columns=[
        "InvoiceNo", "StockCode", "Description", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Country",
    ])
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["CustomerID"] = df["CustomerID"].astype("Int64")
    return df
