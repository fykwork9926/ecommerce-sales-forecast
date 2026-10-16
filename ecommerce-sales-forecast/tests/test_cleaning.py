"""Testes da limpeza e detecção de anomalias."""

import unittest

from salesforecast.cleaning import clean_transactions
from tests.helpers import make_raw

DAY = "2011-01-10 10:00"


class TestCleaning(unittest.TestCase):
    def setUp(self) -> None:
        self.result = clean_transactions(make_raw([
            ("1", "85123A", "HEART", 6, DAY, 2.0, 1, "UK"),
            ("1", "85123A", "HEART", 6, DAY, 2.0, 1, "UK"),   # duplicata
            ("2", "22423", "CAKESTAND", 80, DAY, 10.0, 2, "UK"),
            ("C3", "22423", "CAKESTAND", -80, DAY, 10.0, 2, "UK"),
            ("4", "22111", "ADJUST", -5, DAY, 1.0, None, "UK"),
            ("5", "22222", "FREE GIFT", 1, DAY, 0.0, 3, "UK"),
            ("6", "POST", "POSTAGE", 1, DAY, 18.0, 4, "France"),
            ("7", "22333", "MUG", 2, DAY, 3.0, None, "UK"),
        ]))

    def test_anomaly_counts(self) -> None:
        report = self.result.report
        self.assertEqual(report.duplicates, 1)
        self.assertEqual(report.cancellations, 1)
        self.assertEqual(report.cancelled_value, 800.0)
        self.assertEqual(report.negative_adjustments, 1)
        self.assertEqual(report.non_positive_price, 1)
        self.assertEqual(report.non_product_codes, 1)
        self.assertEqual(report.matched_cancelled_sales, 1)
        self.assertEqual(report.missing_customer, 1)

    def test_only_valid_sales_remain(self) -> None:
        sales = self.result.sales
        self.assertEqual(sorted(sales["InvoiceNo"]), ["1", "7"])
        self.assertEqual(sales["Revenue"].sum(), 12.0 + 6.0)

    def test_invalid_factor_raises(self) -> None:
        with self.assertRaises(ValueError):
            clean_transactions(make_raw([]), outlier_factor=0)


if __name__ == "__main__":
    unittest.main()
