"""Previsão de vendas semanais com NumPy.

Quatro modelos simples competem entre si. Para escolher o melhor de forma
honesta, fazemos um *backtest*: escondemos as últimas semanas, treinamos
com o restante e medimos o erro de cada modelo nas semanas escondidas.
O vencedor é treinado novamente com a série inteira para prever o futuro.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

Model = Callable[[np.ndarray, int], np.ndarray]


def naive_forecast(history: np.ndarray, horizon: int) -> np.ndarray:
    """Repete o último valor observado (referência mínima)."""
    return np.full(horizon, history[-1], dtype=float)


def moving_average_forecast(history: np.ndarray, horizon: int,
                            window: int = 4) -> np.ndarray:
    """Média das últimas `window` semanas."""
    return np.full(horizon, history[-window:].mean(), dtype=float)


def linear_trend_forecast(history: np.ndarray,
                          horizon: int) -> np.ndarray:
    """Reta ajustada por mínimos quadrados (np.polyfit) e projetada."""
    x = np.arange(len(history))
    slope, intercept = np.polyfit(x, history, deg=1)
    future_x = np.arange(len(history), len(history) + horizon)
    return slope * future_x + intercept


def _holt_fit(history: np.ndarray, alpha: float,
              beta: float) -> tuple[float, float, float]:
    """Ajusta o método de Holt; devolve (nível, tendência, erro quadrático)."""
    level, trend = history[0], history[1] - history[0]
    sse = 0.0
    for value in history[1:]:
        prediction = level + trend
        sse += (value - prediction) ** 2
        new_level = alpha * value + (1 - alpha) * prediction
        trend = beta * (new_level - level) + (1 - beta) * trend
        level = new_level
    return level, trend, sse


def holt_forecast(history: np.ndarray, horizon: int) -> np.ndarray:
    """Suavização exponencial dupla (Holt): nível + tendência.

    Os parâmetros alpha e beta são escolhidos por busca em grade,
    minimizando o erro de previsão um passo à frente no histórico.
    """
    grid = np.linspace(0.1, 0.9, 9)
    best = min(
        ((a, b) for a in grid for b in grid),
        key=lambda params: _holt_fit(history, *params)[2],
    )
    level, trend, _ = _holt_fit(history, *best)
    return level + trend * np.arange(1, horizon + 1)


MODELS: dict[str, Model] = {
    "Ingênuo (última semana)": naive_forecast,
    "Média móvel (4 semanas)": moving_average_forecast,
    "Tendência linear": linear_trend_forecast,
    "Holt (suavização exponencial)": holt_forecast,
}


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Erro absoluto médio, na mesma unidade da receita."""
    return float(np.mean(np.abs(actual - predicted)))


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Erro percentual absoluto médio (ignora semanas com receita zero)."""
    mask = actual != 0
    if not mask.any():
        return float("nan")
    errors = np.abs((actual[mask] - predicted[mask]) / actual[mask])
    return float(np.mean(errors) * 100)


@dataclass
class ModelScore:
    """Desempenho de um modelo no backtest."""

    name: str
    mae: float
    mape: float


@dataclass
class ForecastResult:
    """Tudo o que é necessário para reportar e plotar a previsão."""

    history: pd.Series
    scores: list[ModelScore]
    best_model: str
    backtest: pd.Series
    forecast: pd.DataFrame


def backtest_and_forecast(series: pd.Series, test_weeks: int = 8,
                          horizon: int = 8) -> ForecastResult:
    """Compara os modelos no backtest e prevê `horizon` semanas futuras."""
    if test_weeks < 1 or horizon < 1:
        raise ValueError("test_weeks e horizon devem ser maiores que zero.")
    if len(series) < test_weeks + 8:
        raise ValueError(
            f"série curta demais: {len(series)} semanas; são necessárias "
            f"pelo menos {test_weeks + 8}."
        )

    values = series.to_numpy(dtype=float)
    train, test = values[:-test_weeks], values[-test_weeks:]

    scores, predictions = [], {}
    for name, model in MODELS.items():
        predicted = np.clip(model(train, test_weeks), 0, None)
        predictions[name] = predicted
        scores.append(ModelScore(name, round(mae(test, predicted), 2),
                                 round(mape(test, predicted), 2)))
    scores.sort(key=lambda score: score.mae)
    best = scores[0].name

    # Intervalo aproximado de 95%: ±1,96 desvio padrão dos erros do backtest.
    residual_std = float(np.std(test - predictions[best]))
    future = np.clip(MODELS[best](values, horizon), 0, None)
    future_index = pd.date_range(series.index[-1] + pd.Timedelta(weeks=1),
                                 periods=horizon, freq="7D")
    forecast = pd.DataFrame({
        "Forecast": future,
        "Lower": np.clip(future - 1.96 * residual_std, 0, None),
        "Upper": future + 1.96 * residual_std,
    }, index=future_index).round(2)
    forecast.index.name = "WeekStart"

    backtest = pd.Series(predictions[best], index=series.index[-test_weeks:],
                         name="Backtest")
    return ForecastResult(series, scores, best, backtest, forecast)
