"""Testes da segmentação RFM, categorização e análises."""

import unittest

import pandas as pd

from salesforecast.analysis import country_summary, weekly_revenue
from salesforecast.categorization import (abc_class,
                                          categorize_descriptions,
                                          product_table)
from salesforecast.cleaning import clean_transactions
from salesforecast.segmentation import rfm_table
from tests.helpers import make_raw


def sample_sales() -> pd.DataFrame:
    """10 clientes: o cliente 1 compra muito e recentemente."""
    rows = []
    for i in range(1, 11):
        date = pd.Timestamp("2011-12-01") - pd.Timedelta(days=i * 20)
        for order in range(11 - i):
            rows.append((f"{i}{order}", "22423", "CAKESTAND", 1,
                         date, 10.0 * (11 - i), i, "UK"))
    return clean_transactions(make_raw(rows)).sales


class TestRFM(unittest.TestCase):
    def test_best_and_worst_customers(self) -> None:
        rfm = rfm_table(sample_sales())
        self.assertEqual(rfm.loc[1, "Segment"], "Campeões")
        self.assertEqual(rfm.loc[10, "Segment"], "Hibernando")
        self.assertEqual(rfm.loc[1, "Frequency"], 10)

    def test_no_customers_raises(self) -> None:
        sales = sample_sales().assign(CustomerID=pd.NA)
        with self.assertRaises(ValueError):
            rfm_table(sales)


class TestCategorization(unittest.TestCase):
    def test_keywords_and_priority(self) -> None:
        descriptions = pd.Series(["CHRISTMAS LIGHTS", "RED MUGS",
                                  "JUMBO BAG RED", "XYZ QWERTY"])
        self.assertEqual(categorize_descriptions(descriptions).tolist(),
                         ["Natal e festas", "Cozinha e mesa", "Bolsas",
                          "Outros"])

    def test_whole_word_match(self) -> None:
        # "PEN" não pode capturar "PENDANT".
        result = categorize_descriptions(pd.Series(["SILVER PENDANT"]))
        self.assertNotEqual(result.iloc[0], "Papelaria")

    def test_abc_class(self) -> None:
        revenue = pd.Series({"a": 80.0, "b": 15.0, "c": 5.0})
        self.assertEqual(abc_class(revenue).tolist(), ["A", "B", "C"])

    def test_product_table_has_all_features(self) -> None:
        products = product_table(sample_sales())
        for column in ("Category", "PriceBand", "ABC"):
            self.assertIn(column, products.columns)


class TestAnalysis(unittest.TestCase):
    def test_country_summary_average_order(self) -> None:
        summary = country_summary(sample_sales(), min_orders=1)
        self.assertEqual(summary.loc["UK", "Orders"], 55)

    def test_weekly_revenue_drops_partial_weeks(self) -> None:
        sales = pd.DataFrame({
            "InvoiceDate": pd.date_range("2011-01-05", "2011-02-02",
                                         freq="D"),
            "Revenue": 1.0,
        })
        weekly = weekly_revenue(sales)
        self.assertTrue((weekly == 7.0).all())


if __name__ == "__main__":
    unittest.main()
