"""Constantes e configurações usadas em todo o projeto."""

from pathlib import Path

# Cópia pública do dataset "Online Retail" (UCI Machine Learning Repository),
# hospedada no repositório do livro "Spark: The Definitive Guide".
DATASET_URL = (
    "https://raw.githubusercontent.com/databricks/"
    "Spark-The-Definitive-Guide/master/data/retail-data/all/"
    "online-retail-dataset.csv"
)
DEFAULT_DATA_PATH = Path("data/online_retail.csv")
DEFAULT_REPORTS_DIR = Path("reports")

# Colunas obrigatórias do dataset.
REQUIRED_COLUMNS = (
    "InvoiceNo", "StockCode", "Description", "Quantity",
    "InvoiceDate", "UnitPrice", "CustomerID", "Country",
)

# Formato de data do CSV (ex.: "12/1/2010 8:26" = mês/dia/ano).
DATE_FORMAT = "%m/%d/%Y %H:%M"

# Códigos de produto reais começam com 5 dígitos (ex.: 85123A).
# Códigos como POST, M, DOT, BANK CHARGES são taxas/ajustes, não produtos.
PRODUCT_CODE_PATTERN = r"^\d{5}"
