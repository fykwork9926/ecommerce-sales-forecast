"""Testes da leitura do dataset."""

import tempfile
import unittest
from pathlib import Path

from salesforecast.data_loader import DataLoadError, load_transactions

HEADER = ("InvoiceNo,StockCode,Description,Quantity,InvoiceDate,"
          "UnitPrice,CustomerID,Country\n")


class TestLoadTransactions(unittest.TestCase):
    def _write(self, content: str, name: str = "data.csv") -> Path:
        path = Path(self.tmp.name) / name
        path.write_text(content, encoding="utf-8")
        return path

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_reads_and_converts_types(self) -> None:
        path = self._write(HEADER + "536365,85123A,HEART,6,"
                           "12/1/2010 8:26,2.55,17850,United Kingdom\n")
        df = load_transactions(path)
        self.assertEqual(df.loc[0, "InvoiceDate"].month, 12)
        self.assertEqual(df.loc[0, "CustomerID"], 17850)
        self.assertEqual(df.loc[0, "StockCode"], "85123A")

    def test_invalid_values_become_nan(self) -> None:
        path = self._write(HEADER + "1,85123A,X,abc,data-ruim,2.5,,UK\n")
        df = load_transactions(path)
        self.assertTrue(df[["Quantity", "InvoiceDate"]].isna().all().all())

    def test_missing_columns_raise(self) -> None:
        path = self._write("a,b\n1,2\n")
        with self.assertRaises(DataLoadError):
            load_transactions(path)

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(DataLoadError):
            load_transactions("nao/existe.csv")

    def test_unsupported_extension_raises(self) -> None:
        with self.assertRaises(DataLoadError):
            load_transactions(self._write("x", name="dados.txt"))


if __name__ == "__main__":
    unittest.main()
