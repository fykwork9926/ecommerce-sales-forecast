"""Categorização dos produtos por três características diferentes.

1. Categoria temática: palavras-chave na descrição do produto.
2. Faixa de preço: econômico, intermediário ou premium (tercis).
3. Curva ABC: importância do produto na receita total.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

# A ordem importa: o produto recebe a PRIMEIRA categoria que combinar.
# Ex.: "CHRISTMAS LIGHTS" fica em "Natal e festas", não em "Iluminação".
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Natal e festas": ("CHRISTMAS", "XMAS", "EASTER", "PARTY", "BIRTHDAY",
                       "HALLOWEEN", "ADVENT", "BUNTING", "SANTA"),
    "Iluminação": ("LIGHT", "LANTERN", "CANDLE", "T-LIGHT", "LAMP",
                   "NIGHTLIGHT"),
    "Cozinha e mesa": ("MUG", "CUP", "PLATE", "BOWL", "TEA", "TEAPOT",
                       "CAKE", "BAKING", "LUNCH", "JAR", "SPOON", "KITCHEN",
                       "BOTTLE", "TRAY", "NAPKIN", "TIN", "CUTLERY",
                       "APRON", "CAKESTAND", "RECIPE", "COASTER",
                       "TEACUP", "SAUCER", "JAM", "SNACK", "BREAD", "JUG",
                       "MOULD", "DISH", "EGG", "PAN", "POPCORN", "FOOD",
                       "PICNIC", "GLASS", "STRAW", "DOILY"),
    "Bolsas": ("BAG", "PURSE", "SHOPPER", "TOTE", "BACKPACK", "HANDBAG"),
    "Papelaria": ("CARD", "PAPER", "NOTEBOOK", "PEN", "PENCIL", "STICKER",
                  "WRAP", "ENVELOPE", "DIARY", "CALENDAR", "NOTEPAD",
                  "TAPE"),
    "Brinquedos e jogos": ("TOY", "GAME", "DOLL", "PUZZLE", "SPACEBOY",
                           "DOMINO", "SKITTLES", "BALLOON", "JIGSAW",
                           "BLOCK", "SKIPPING", "FELTCRAFT", "PAINT", "KIT",
                           "GLIDER", "DOLLY", "CRAYON", "SPINNING", "TOP"),
    "Jardim": ("GARDEN", "PLANT", "WATERING", "BIRD", "PLANTER", "SEED"),
    "Joias e acessórios": ("NECKLACE", "BRACELET", "EARRINGS", "RING",
                           "HAIR", "UMBRELLA", "BROOCH", "KEYRING",
                           "PARASOL", "WARMER", "FAN", "LIP", "GLOSS",
                           "CHARM", "TISSUES", "MIRROR", "COMPACT"),
    "Casa e organização": ("CABINET", "DRAWER", "STORAGE", "RACK", "BASKET",
                           "KNOB", "CHEST", "CASE", "BOARD", "MEMOBOARD",
                           "PEGS", "MAGNET", "BIN", "BOXES", "SHELF",
                           "HOLDER", "LAUNDRY", "DOORMAT", "TISSUE"),
    "Decoração": ("FRAME", "SIGN", "HEART", "CUSHION", "CLOCK", "ORNAMENT",
                  "DECORATION", "DOORSTOP", "HOOK", "GARLAND", "ART",
                  "WREATH", "VASE", "HANGING", "BOX", "INCENSE", "RIBBON",
                  "FLOWER", "BUTTERFLY", "STAR", "PHOTO", "BUNNY"),
}
DEFAULT_CATEGORY = "Outros"
PRICE_BANDS = ["Econômico", "Intermediário", "Premium"]


def _keyword_regex(keywords: tuple[str, ...]) -> str:
    """Palavra inteira, aceitando plural com S (ex.: MUG e MUGS)."""
    words = "|".join(re.escape(word) for word in keywords)
    return rf"\b(?:{words})S?\b"


def categorize_descriptions(descriptions: pd.Series) -> pd.Series:
    """Atribui uma categoria temática a cada descrição."""
    text = descriptions.fillna("").str.upper()
    categories = pd.Series(DEFAULT_CATEGORY, index=descriptions.index)
    for category, keywords in CATEGORY_KEYWORDS.items():
        match = text.str.contains(_keyword_regex(keywords), regex=True)
        unassigned = categories == DEFAULT_CATEGORY
        categories[match & unassigned] = category
    return categories


def abc_class(revenue: pd.Series) -> pd.Series:
    """Curva ABC: A = 80% da receita, B = próximos 15%, C = últimos 5%."""
    ordered = revenue.sort_values(ascending=False)
    cumulative = ordered.cumsum() / ordered.sum()
    # Usa a participação ANTES do produto, para o primeiro sempre ser A.
    previous = cumulative.shift(fill_value=0)
    classes = np.select([previous < 0.80, previous < 0.95], ["A", "B"], "C")
    return pd.Series(classes, index=ordered.index).reindex(revenue.index)


def product_table(sales: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por produto com métricas e as três categorizações."""
    if sales.empty:
        raise ValueError("não há vendas para categorizar.")

    # Um mesmo código pode ter descrições levemente diferentes;
    # usamos a mais frequente.
    descriptions = (
        sales.groupby(["StockCode", "Description"]).size()
        .reset_index(name="n").sort_values("n")
        .drop_duplicates("StockCode", keep="last")
        .set_index("StockCode")["Description"]
    )
    products = sales.groupby("StockCode").agg(
        MedianPrice=("UnitPrice", "median"),
        Quantity=("Quantity", "sum"),
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
    )
    products.insert(0, "Description", descriptions.reindex(products.index))
    products["Category"] = categorize_descriptions(products["Description"])

    bands = min(3, len(products))
    ranks = products["MedianPrice"].rank(method="first")
    products["PriceBand"] = pd.qcut(ranks, bands,
                                    labels=PRICE_BANDS[:bands]).astype(str)
    products["ABC"] = abc_class(products["Revenue"])
    return products.sort_values("Revenue", ascending=False).round(2)


def category_summary(products: pd.DataFrame) -> pd.DataFrame:
    """Receita e quantidade de produtos por categoria temática."""
    summary = products.groupby("Category").agg(
        Products=("Revenue", "size"),
        Revenue=("Revenue", "sum"),
        ClassA=("ABC", lambda s: int((s == "A").sum())),
    )
    summary["Revenue"] = summary["Revenue"].round(2)
    share = summary["Revenue"] / products["Revenue"].sum()
    summary["RevenueShare"] = share.round(4)
    return summary.sort_values("Revenue", ascending=False)
