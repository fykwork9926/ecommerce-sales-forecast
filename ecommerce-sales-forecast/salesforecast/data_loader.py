"""Download e leitura do dataset de transações."""

from __future__ import annotations

import shutil
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

from salesforecast.config import DATASET_URL, DATE_FORMAT, REQUIRED_COLUMNS


class DataLoadError(Exception):
    """Erro levantado quando o dataset não pode ser obtido ou lido."""


def download_dataset(destination: str | Path, url: str = DATASET_URL,
                     timeout: int = 60) -> Path:
    """Baixa o dataset para `destination`.

    O download é feito em um arquivo temporário e só depois renomeado,
    para que uma queda de conexão não deixe um CSV pela metade.
    """
    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    temp = dest.with_suffix(dest.suffix + ".part")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response, \
                temp.open("wb") as file:
            shutil.copyfileobj(response, file)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        temp.unlink(missing_ok=True)
        raise DataLoadError(f"falha no download: {exc}") from exc
    temp.replace(dest)
    return dest


def load_transactions(path: str | Path) -> pd.DataFrame:
    """Lê o dataset (CSV ou Excel) e converte as colunas para os tipos certos.

    Valores impossíveis de converter (data ou número inválido) viram NaN/NaT
    e são removidos depois, na etapa de limpeza, onde também são contados.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise DataLoadError(
            f"arquivo não encontrado: {file_path}. "
            "Rode 'python -m salesforecast download' primeiro."
        )

    text_columns = {"InvoiceNo": str, "StockCode": str,
                    "Description": str, "Country": str}
    suffix = file_path.suffix.lower()
    try:
        if suffix == ".csv":
            df = pd.read_csv(file_path, dtype=text_columns,
                             encoding_errors="replace")
        elif suffix in (".xlsx", ".xls"):
            df = pd.read_excel(file_path, dtype=text_columns)
        else:
            raise DataLoadError(f"formato não suportado: '{suffix}' "
                                "(use .csv ou .xlsx)")
    except ImportError as exc:
        raise DataLoadError("para ler Excel instale: pip install openpyxl"
                            ) from exc
    except (pd.errors.ParserError, pd.errors.EmptyDataError,
            UnicodeDecodeError, OSError) as exc:
        raise DataLoadError(f"não foi possível ler {file_path}: {exc}"
                            ) from exc

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise DataLoadError(f"colunas ausentes no dataset: {missing}")

    df = df[list(REQUIRED_COLUMNS)].copy()
    if not pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"],
                                           format=DATE_FORMAT,
                                           errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"],
                                     errors="coerce").astype("Int64")
    return df
