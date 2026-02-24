from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

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
            if np.isnan(res) or np.isinf(res):
                return 0.0
            return res
        except (TypeError, ValueError):
            return 0.0

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
            value=safe_float(mean_absolute_percentage_error(y_true, y_pred)),
        ),
    ]
    return metrics


class InternalForecaster(ABC):
    """Base class for internal forecast implementations."""

    # Rashomon Complexity Score (0-5 scale)
    complexity_score: float = 0
    # Archetype Description (When this model wins)
    archetype: str = "Baseline"
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
        Generate forecasts with multi-layer confidence intervals.

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
        Calculate multiple levels of confidence intervals using standard normal distribution.
        """
        # We need layers for 30%, 60%, and 80%
        widths = [0.30, 0.60, 0.80]
        results = {}
        for width in widths:
            alpha = 1 - width
            z_score = stats.norm.ppf(1 - alpha / 2)
            margin = z_score * residuals_std
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
        Legacy single-layer interval calculator.
        """
        alpha = 1 - interval_width
        z_score = stats.norm.ppf(1 - alpha / 2)
        margin = z_score * residuals_std
        lower = predictions - margin
        upper = predictions + margin
        return lower, upper
