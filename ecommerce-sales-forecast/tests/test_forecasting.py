"""Testes dos modelos de previsão e do backtest."""

import unittest

import numpy as np
import pandas as pd

from salesforecast.forecasting import (backtest_and_forecast,
                                       linear_trend_forecast, mae, mape,
                                       moving_average_forecast,
                                       naive_forecast)


class TestModels(unittest.TestCase):
    def test_naive_and_moving_average(self) -> None:
        history = np.array([1.0, 2.0, 3.0, 4.0, 10.0])
        self.assertEqual(naive_forecast(history, 2).tolist(), [10.0, 10.0])
        self.assertAlmostEqual(moving_average_forecast(history, 1)[0], 4.75)

    def test_linear_trend_continues_line(self) -> None:
        history = np.array([10.0, 20.0, 30.0, 40.0])
        np.testing.assert_allclose(linear_trend_forecast(history, 2),
                                   [50.0, 60.0])

    def test_metrics(self) -> None:
        actual = np.array([100.0, 200.0])
        predicted = np.array([110.0, 180.0])
        self.assertAlmostEqual(mae(actual, predicted), 15.0)
        self.assertAlmostEqual(mape(actual, predicted), 10.0)


class TestBacktest(unittest.TestCase):
    def _series(self, values: np.ndarray) -> pd.Series:
        index = pd.date_range("2011-01-03", periods=len(values), freq="7D")
        return pd.Series(values, index=index)

    def test_trend_wins_on_linear_series(self) -> None:
        series = self._series(np.arange(30, dtype=float) * 100 + 1000)
        result = backtest_and_forecast(series, test_weeks=6, horizon=4)
        self.assertIn(result.best_model, ("Tendência linear",
                                          "Holt (suavização exponencial)"))
        self.assertEqual(len(result.forecast), 4)
        self.assertEqual(result.forecast.index[0],
                         series.index[-1] + pd.Timedelta(weeks=1))
        self.assertAlmostEqual(result.forecast["Forecast"].iloc[0], 4000.0,
                               delta=1)

    def test_forecast_is_never_negative(self) -> None:
        series = self._series(np.linspace(5000, 100, 30))
        result = backtest_and_forecast(series, test_weeks=6, horizon=10)
        self.assertTrue((result.forecast >= 0).all().all())

    def test_short_series_raises(self) -> None:
        with self.assertRaises(ValueError):
            backtest_and_forecast(self._series(np.ones(5)), test_weeks=4)


if __name__ == "__main__":
    unittest.main()
