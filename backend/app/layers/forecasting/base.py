from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series) -> List[ForecastMetric]:
    def safe_float(val):
        try:
            res = float(val)
            if np.isnan(res):
                return float("inf")
            return res
        except (TypeError, ValueError):
            return float("inf")

    metrics = [
        ForecastMetric(
            name="MAE", value=safe_float(mean_absolute_error(y_true, y_pred))
        ),
        ForecastMetric(
            name="RMSE",
            value=safe_float(np.sqrt(mean_squared_error(y_true, y_pred))),
        ),
        ForecastMetric(
            name="MAPE",
            value=safe_float(mean_absolute_percentage_error(y_true, y_pred) * 100),
        ),
    ]
    return metrics


def walk_forward_backtest(
    df: pd.DataFrame,
    time_col: str,
    target_col: str,
    horizon_steps: int,
    fit_predict_fn: Callable[[pd.DataFrame, pd.DataFrame], pd.Series],
    min_train_size: Optional[int] = None,
    max_windows: int = 10,
) -> Tuple[pd.Series, pd.Series]:
    """
    End-anchored expanding-window walk-forward backtest.

    The backtest is anchored on the most recent data. The training set grows by
    ``horizon_steps`` each window. Validation is always ``horizon_steps`` except
    possibly the last partial chunk. The number of windows is capped by
    ``max_windows`` and available data.

    Parameters
    ----------
    df : pd.DataFrame
        Prepared DataFrame with ``time_col`` as index or column.
    time_col : str
        Name of the datetime column (used only if it is still a column).
    target_col : str
        Name of the target series.
    horizon_steps : int
        Forecast horizon – used as the step size for each window.
    fit_predict_fn : callable
        ``fit_predict_fn(train_df, val_df) -> pd.Series`` aligned to
        ``val_df.index``.
    min_train_size : int, optional
        Minimum rows required in the first training window. Defaults to
        ``max(2 * horizon_steps, 20)``.
    max_windows : int, optional
        Hard cap on backtest windows to keep runtime bounded. Defaults to 10.

    Returns
    -------
    Tuple[pd.Series, pd.Series]
        (all_predictions, all_actuals) with DatetimeIndex.
    """
    # Ensure datetime index
    if time_col in df.columns:
        df = df.set_index(time_col)
    df.index = pd.to_datetime(df.index)

    n = len(df)
    min_train_size = min_train_size or max(2 * horizon_steps, 20)

    # Edge case: not enough data for a meaningful walk-forward backtest.
    # Fall back to a single train/val split.
    if n <= min_train_size + 1:
        split_idx = max(1, int(n * 0.8))
        train_df = df.iloc[:split_idx]
        val_df = df.iloc[split_idx:]
        if len(val_df) == 0:
            empty_idx = pd.DatetimeIndex([], dtype="datetime64[ns]")
            return pd.Series([], dtype=float, index=empty_idx), pd.Series(
                [], dtype=float, index=empty_idx
            )
        preds = fit_predict_fn(train_df, val_df)
        return preds, val_df[target_col]

    available_windows = max(1, (n - min_train_size) // horizon_steps)
    n_windows = min(max_windows, available_windows)
    total_val_len = n_windows * horizon_steps
    start_idx = max(min_train_size, n - total_val_len)

    all_preds: List[float] = []
    all_actuals: List[float] = []

    for w in range(n_windows):
        train_end = start_idx + w * horizon_steps
        val_end = min(train_end + horizon_steps, n)
        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]

        preds = fit_predict_fn(train_df, val_df)
        # Guard against length mismatches (e.g. truncated by regressor)
        chunk_actuals = val_df[target_col].iloc[: len(preds)].values
        all_preds.extend(preds.values)
        all_actuals.extend(chunk_actuals)

    val_index = df.index[start_idx : start_idx + len(all_preds)]
    return pd.Series(all_preds, index=val_index), pd.Series(
        all_actuals, index=val_index
    )


class InternalForecaster(ABC):
    """Base class for internal forecast implementations."""

    # Rashomon Complexity Score (0-5 scale)
    complexity_score: float = 0
    # Archetype Description (When this model wins)
    archetype: str = "Baseline"
    # Whether this model can consume covariate columns
    supports_covariates: bool = False
    # Residual standard deviation for interval calculation (set during fit)
    residuals_std: float = 0.0
    # Hold-out validation predictions (set during fit)
    validation_predictions: Optional[pd.Series] = None
    # Hold-out validation actuals (set during fit)
    validation_actuals: Optional[pd.Series] = None

    @abstractmethod
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        raise NotImplementedError

    @abstractmethod
    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        """
        Generate forecasts with multi-layer prediction intervals.

        Returns DataFrame with columns:
        ['date', 'median_forecast', 'conf_30_lower', 'conf_30_upper',
         'conf_60_lower', 'conf_60_upper', 'conf_80_lower', 'conf_80_upper']
        """
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self) -> ModelMetadata:
        raise NotImplementedError

    def _calculate_multi_layer_intervals(
        self,
        predictions: np.ndarray,
        residuals_std: float,
    ) -> Dict[str, np.ndarray]:
        """
        Calculate multiple levels of prediction intervals using standard normal distribution,
        scaling uncertainty with sqrt(h) to account for increasing error over time.
        """
        # We need layers for 30%, 60%, and 80%
        widths = [0.30, 0.60, 0.80]
        results = {}
        
        # Calculate scaling factor: sqrt(1, 2, 3... horizon)
        # This is a common heuristic for random-walk like error growth
        horizon = len(predictions)
        steps = np.arange(1, horizon + 1)
        scaling = np.sqrt(steps)
        
        for width in widths:
            alpha = 1 - width
            z_score = stats.norm.ppf(1 - alpha / 2)
            # Apply scaling to the margin
            margin = z_score * residuals_std * scaling
            label = int(width * 100)
            results[f"conf_{label}_lower"] = predictions - margin
            results[f"conf_{label}_upper"] = predictions + margin
        return results

    def _calculate_intervals(
        self,
        predictions: np.ndarray,
        interval_width: float,
        residuals_std: float,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Legacy single-layer interval calculator with horizon scaling.
        """
        horizon = len(predictions)
        steps = np.arange(1, horizon + 1)
        scaling = np.sqrt(steps)
        
        alpha = 1 - interval_width
        z_score = stats.norm.ppf(1 - alpha / 2)
        margin = z_score * residuals_std * scaling
        lower = predictions - margin
        upper = predictions + margin
        return lower, upper
