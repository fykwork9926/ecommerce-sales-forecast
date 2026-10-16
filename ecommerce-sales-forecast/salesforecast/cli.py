"""Interface de linha de comando (CLI) do SalesForecast."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from salesforecast import __version__
from salesforecast.analysis import (country_summary, monthly_summary,
                                    weekly_revenue)
from salesforecast.categorization import category_summary, product_table
from salesforecast.cleaning import clean_transactions
from salesforecast.config import DEFAULT_DATA_PATH, DEFAULT_REPORTS_DIR
from salesforecast.data_loader import (DataLoadError, download_dataset,
                                       load_transactions)
from salesforecast.forecasting import backtest_and_forecast
from salesforecast.reporter import ReportError, export_tables, print_report
from salesforecast.segmentation import rfm_table, segment_summary
from salesforecast import visualization as viz

EXIT_OK = 0
EXIT_ERROR = 1


def _positive_int(value: str) -> int:
    """Validador do argparse que aceita apenas inteiros positivos."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"'{value}' não é um número inteiro.") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("o valor deve ser maior que zero.")
    return number


def _error(message: str) -> None:
    print(f"Erro: {message}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """Define os comandos e opções aceitos pela CLI."""
    parser = argparse.ArgumentParser(
        prog="salesforecast",
        description="Análise, segmentação e previsão de vendas "
                    "de um e-commerce.",
    )
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    download = sub.add_parser("download", help="baixa o dataset público")
    download.add_argument("-o", "--output", type=Path,
                          default=DEFAULT_DATA_PATH,
                          help=f"destino (padrão: {DEFAULT_DATA_PATH})")
    download.set_defaults(func=cmd_download)

    run = sub.add_parser("run", help="executa todas as análises")
    run.add_argument("datafile", type=Path, nargs="?",
                     default=DEFAULT_DATA_PATH,
                     help=f"CSV ou XLSX (padrão: {DEFAULT_DATA_PATH})")
    run.add_argument("--horizon", type=_positive_int, default=8,
                     help="semanas a prever (padrão: 8)")
    run.add_argument("--test-weeks", type=_positive_int, default=8,
                     help="semanas usadas no backtest (padrão: 8)")
    run.add_argument("--top", type=_positive_int, default=5,
                     help="itens nos rankings (padrão: 5)")
    run.add_argument("-o", "--output", type=Path,
                     default=DEFAULT_REPORTS_DIR,
                     help=f"pasta de saída (padrão: {DEFAULT_REPORTS_DIR})")
    run.add_argument("--no-plots", action="store_true",
                     help="não gera os gráficos PNG")
    run.set_defaults(func=cmd_run)
    return parser


def cmd_download(args: argparse.Namespace) -> int:
    """Baixa o dataset."""
    print("Baixando o dataset (~45 MB)...")
    try:
        path = download_dataset(args.output)
    except DataLoadError as exc:
        _error(str(exc))
        return EXIT_ERROR
    print(f"Dataset salvo em: {path}")
    return EXIT_OK


def cmd_run(args: argparse.Namespace) -> int:
    """Fluxo completo: carregar → limpar → analisar → prever → reportar."""
    try:
        print(f"Lendo {args.datafile}...")
        raw = load_transactions(args.datafile)
        cleaned = clean_transactions(raw)
        sales = cleaned.sales
        if sales.empty:
            _error("nenhuma venda válida após a limpeza.")
            return EXIT_ERROR

        monthly = monthly_summary(sales)
        countries = country_summary(sales)
        rfm = rfm_table(sales)
        segments = segment_summary(rfm)
        products = product_table(sales)
        categories = category_summary(products)
        result = backtest_and_forecast(weekly_revenue(sales),
                                       test_weeks=args.test_weeks,
                                       horizon=args.horizon)
    except (DataLoadError, ValueError) as exc:
        _error(str(exc))
        return EXIT_ERROR

    print_report(cleaned.report, monthly, countries, segments, categories,
                 products, result, top=args.top)

    anomalies = pd.DataFrame(cleaned.report.as_rows(),
                             columns=["Anomalia", "Valor"]
                             ).set_index("Anomalia")
    try:
        saved = export_tables(args.output, {
            "anomalias": anomalies,
            "receita_mensal": monthly,
            "paises": countries,
            "clientes_rfm": rfm,
            "segmentos": segments,
            "produtos": products,
            "categorias": categories,
            "previsao": result.forecast,
        })
        if not args.no_plots:
            figures = args.output / "figures"
            saved += [
                viz.plot_monthly_revenue(monthly,
                                         figures / "receita_mensal.png"),
                viz.plot_forecast(result, figures / "previsao.png"),
                viz.plot_horizontal_bars(
                    countries["AvgOrderValue"].head(10),
                    "Ticket médio por país (top 10)",
                    figures / "ticket_medio_paises.png"),
                viz.plot_horizontal_bars(
                    segments["Revenue"], "Receita por segmento de clientes",
                    figures / "segmentos_rfm.png"),
                viz.plot_horizontal_bars(
                    categories["Revenue"], "Receita por categoria",
                    figures / "categorias.png"),
            ]
    except (ReportError, OSError) as exc:
        _error(str(exc))
        return EXIT_ERROR

    print(f"{len(saved)} arquivos salvos em: {args.output}/")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da aplicação. Retorna o código de saída."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.", file=sys.stderr)
        return 130
