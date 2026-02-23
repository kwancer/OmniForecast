from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from pmdarima import auto_arima
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from xgboost import XGBRegressor

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata


def calculate_metrics(y_true: pd.Series, y_pred: pd.Series) -> List[ForecastMetric]:
    def safe_float(val):
        try:
            res = float(val)
            if np.isnan(res) or np.isinf(res):
                return 0.0
            return res
        except Exception:
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
        pass

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
        pass

    @abstractmethod
    def get_metadata(self) -> ModelMetadata:
        pass

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


class NaiveForecaster(InternalForecaster):
    complexity_score = 0
    archetype = "The Flat Line / Random Walk (Tomorrow = Today)"

    def __init__(self):
        self.last_value = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None
        self.residuals_std = 0.0

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        split_idx = int(len(df) * 0.8)
        if split_idx == 0:
            split_idx = 1
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        if len(val) == 0:
            # No validation data available; return worst-case metrics so that
            # this model is not incorrectly favored during model selection.
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        # Naive: Predict last value of train for all val steps
        last_train_val = train[self.target_col].iloc[-1]
        val_preds = pd.Series([last_train_val] * len(val), index=val.index)

        # Calculate residuals for confidence intervals
        residuals = val[self.target_col] - val_preds
        self.residuals_std = float(residuals.std()) if len(residuals) > 1 else 0.0
        self.validation_predictions = val_preds
        self.validation_actuals = val[self.target_col]

        # Final fit
        self.last_value = df[self.target_col].iloc[-1]

        return calculate_metrics(val[self.target_col], val_preds)

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        predictions = np.array([self.last_value] * horizon)

        # Multi-layer intervals
        intervals = self._calculate_multi_layer_intervals(
            predictions, self.residuals_std
        )

        # Legacy columns for compatibility
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )

        df_data = {
            "date": future_dates,
            "mean": predictions,  # legacy
            "median_forecast": predictions,
            "lower": lower,  # legacy
            "upper": upper,  # legacy
            **intervals,
        }

        # If it's annual data, also add 'year' column to match user request schema
        if self.freq == "A" or self.freq == "Y":
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="Naive Baseline",
            description="Predicts the last observed value for all future time steps.",
            rationale="Used as a baseline. If this wins, the data is likely a Random Walk.",
            educational_video_url="",
        )


class SeasonalNaiveForecaster(InternalForecaster):
    complexity_score = 0.5
    archetype = "Seasonal Random Walk (Tomorrow = Same day last year/season)"

    def __init__(self, season_length=7):
        self.season_length = season_length
        self.history = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None
        self.residuals_std = 0.0

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        if self.freq == "M":
            self.season_length = 12
        elif self.freq == "D":
            self.season_length = 7

        split_idx = int(len(df) * 0.8)
        if split_idx == 0:
            split_idx = 1
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        if len(val) == 0:
            # No validation data available; return worst-case metrics so that
            # this model is not incorrectly favored during model selection.
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        def get_seasonal_preds(history_series, steps):
            preds = []
            for i in range(steps):
                lookback_idx = (i % self.season_length) + 1
                try:
                    preds.append(history_series.iloc[-lookback_idx])
                except IndexError:
                    preds.append(history_series.iloc[-1])
            return preds

        val_preds_list = get_seasonal_preds(train[self.target_col], len(val))
        val_preds = pd.Series(val_preds_list, index=val.index)

        # Calculate residuals for confidence intervals
        residuals = val[self.target_col] - val_preds
        self.residuals_std = float(residuals.std()) if len(residuals) > 1 else 0.0
        self.validation_predictions = val_preds
        self.validation_actuals = val[self.target_col]

        self.history = df[self.target_col]
        return calculate_metrics(val[self.target_col], val_preds)

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        preds = []
        last_season = self.history.iloc[-self.season_length :].values

        for i in range(horizon):
            preds.append(last_season[i % self.season_length])

        predictions = np.array(preds)

        # Multi-layer intervals
        intervals = self._calculate_multi_layer_intervals(
            predictions, self.residuals_std
        )

        # Legacy columns
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )

        df_data = {
            "date": future_dates,
            "mean": predictions,
            "median_forecast": predictions,
            "lower": lower,
            "upper": upper,
            **intervals,
        }

        if self.freq == "A" or self.freq == "Y":
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="Seasonal Naive",
            description="Predicts values from the previous season (e.g. same day last week).",
            rationale="Robust baseline for seasonal data.",
            educational_video_url="",
        )


class ETSForecaster(InternalForecaster):
    """
    Wrapper for statsmodels Exponential Smoothing covering multiple variants.
    """

    def __init__(self, config_name: str, trend=None, damped=False, seasonal=None):
        self.config_name = config_name
        self.trend = trend
        self.damped = damped
        self.seasonal = seasonal

        self.model = None
        self.fit_result = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None

        # Assignments based on complexity
        if seasonal:
            self.complexity_score = 4
            self.archetype = "The Seasonal Specialist (Trend + Seasonality)"
        elif damped:
            self.complexity_score = 3
            self.archetype = "The Realistic Climber (Damped Trend)"
        elif trend:
            self.complexity_score = 2
            self.archetype = "The Steady Climber (Trend, No Seasonality)"
        else:
            self.complexity_score = 1
            self.archetype = "The Flat Line (No Trend, No Seasonality)"

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        split_idx = int(len(df) * 0.8)
        if split_idx == 0:
            split_idx = 1
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        if len(val) == 0:
            # No validation data available; return worst-case metrics so that
            # this model is not incorrectly favored during model selection.
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        try:
            # Determine seasonal_periods only if seasonal is specified
            seasonal_periods = None
            if self.seasonal is not None:
                seasonal_periods = (
                    7 if self.freq == "D" else (12 if self.freq == "M" else None)
                )

            # Train on Training Set
            model = ExponentialSmoothing(
                train[self.target_col],
                trend=self.trend,
                damped_trend=self.damped,
                seasonal=self.seasonal,
                seasonal_periods=seasonal_periods,
                freq=self.freq,
            )
            fit_result = model.fit(optimized=True)
            val_preds = fit_result.forecast(len(val))

            # FIT ON FULL DATA
            self.model = ExponentialSmoothing(
                df[self.target_col],
                trend=self.trend,
                damped_trend=self.damped,
                seasonal=self.seasonal,
                seasonal_periods=seasonal_periods,
                freq=self.freq,
            )
            self.fit_result = self.model.fit(optimized=True)
            self.validation_predictions = val_preds
            self.validation_actuals = val[self.target_col]

            return calculate_metrics(val[self.target_col], val_preds)
        except Exception as e:
            print(f"LOG: Model {self.config_name} failed: {e}")
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
            ]

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if not self.fit_result:
            raise ValueError("Model not fitted.")

        # Point forecast
        forecast_values = self.fit_result.forecast(horizon)
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        # Simulation-based confidence intervals (as requested)
        try:
            # Generate simulation paths
            simulations = self.fit_result.simulate(
                nsimulations=horizon,
                anchor="end",
                repetitions=1000,
            )
            # simulations shape: (horizon, 1000)

            # Calculate required percentiles
            # Median: 50%
            median_vals = np.percentile(simulations, 50, axis=1)

            # Layer 1 (Outer/80%): 10th and 90th
            conf_80_lower = np.percentile(simulations, 10, axis=1)
            conf_80_upper = np.percentile(simulations, 90, axis=1)

            # Layer 2 (Middle/60%): 20th and 80th
            conf_60_lower = np.percentile(simulations, 20, axis=1)
            conf_60_upper = np.percentile(simulations, 80, axis=1)

            # Layer 3 (Inner/30%): 35th and 65th
            conf_30_lower = np.percentile(simulations, 35, axis=1)
            conf_30_upper = np.percentile(simulations, 65, axis=1)

            # Fallback for legacy interval_width
            alpha = 1 - interval_width
            lower = np.percentile(simulations, (alpha / 2) * 100, axis=1)
            upper = np.percentile(simulations, (1 - alpha / 2) * 100, axis=1)

            df_data = {
                "date": future_dates,
                "median_forecast": median_vals,
                "mean": forecast_values.values,  # Keep actual point forecast as mean
                "lower": lower,
                "upper": upper,
                "conf_80_lower": conf_80_lower,
                "conf_80_upper": conf_80_upper,
                "conf_60_lower": conf_60_lower,
                "conf_60_upper": conf_60_upper,
                "conf_30_lower": conf_30_lower,
                "conf_30_upper": conf_30_upper,
            }

            if self.freq == "A" or self.freq == "Y":
                df_data["year"] = [d.year for d in future_dates]

            return pd.DataFrame(df_data)

        except Exception as e:
            print(f"LOG: ETS simulation failed, using point forecast: {e}")
            # Fallback: use residual-based approach if simulation fails
            mean_vals = forecast_values.values
            intervals = self._calculate_multi_layer_intervals(
                mean_vals, self.residuals_std
            )
            lower, upper = self._calculate_intervals(
                mean_vals, interval_width, self.residuals_std
            )

            df_data = {
                "date": future_dates,
                "mean": mean_vals,
                "median_forecast": mean_vals,
                "lower": lower,
                "upper": upper,
                **intervals,
            }
            if self.freq == "A" or self.freq == "Y":
                df_data["year"] = [d.year for d in future_dates]

            return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=f"ETS ({self.config_name})",
            description=f"Exponential Smoothing: {self.config_name}. {self.archetype}",
            rationale=f"Selected due to {self.archetype} characteristics.",
            educational_video_url="https://www.youtube.com/watch?v=Du8h_S_ndRE",
        )


class ARIMAForecaster(InternalForecaster):
    """
    AutoARIMA implementation using pmdarima for fast, automated model selection.
    """

    def __init__(self):
        self.model = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None
        self.residuals_std = 0.0
        self.complexity_score = 1.0  # Default, gets updated in fit()
        self.archetype = "The Autoregressive Pattern (Correlation with Past)"

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df_index = df.set_index(self.time_col)
        self.last_date = df_index.index.max()
        self.freq = pd.infer_freq(df_index.index) or "D"

        split_idx = int(len(df_index) * 0.8)
        if split_idx == 0:
            split_idx = 1
        train, val = df_index.iloc[:split_idx], df_index.iloc[split_idx:]

        if len(val) == 0:
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        # Speed Constraints (Crucial)
        autoarima_params = {
            "stepwise": True,
            "suppress_warnings": True,
            "error_action": "ignore",
            "max_p": 3,
            "max_q": 3,
            "max_d": 2,
        }

        # Seasonal handling: 12 for month, 7 for day
        if self.freq in ["M", "MS", "BM", "BMS"]:
            autoarima_params.update({"seasonal": True, "m": 12, "max_P": 2, "max_Q": 2})
        elif self.freq in ["D", "B"]:
            autoarima_params.update({"seasonal": True, "m": 7, "max_P": 2, "max_Q": 2})

        try:
            # Fit AutoARIMA on 80% training split to generate validation predictions
            temp_model = auto_arima(train[self.target_col], **autoarima_params)
            val_preds = temp_model.predict(n_periods=len(val))

            # Calculate residuals standard deviation for confidence intervals
            residuals = val[self.target_col].values - val_preds
            self.residuals_std = float(np.std(residuals)) if len(residuals) > 1 else 0.0
            self.validation_predictions = pd.Series(val_preds, index=val.index)
            self.validation_actuals = val[self.target_col]

            # Refit the model on the entire 100% dataframe
            self.model = auto_arima(df_index[self.target_col], **autoarima_params)

            # Dynamic Complexity Scoring:
            # 1 + (sum(order) + sum(seasonal_order[:3])) / 6.0

            order = self.model.order
            seasonal_order = self.model.seasonal_order
            raw_complexity = 1 + (sum(order) + sum(seasonal_order[:3])) / 6.0
            self.complexity_score = max(1.0, min(4.0, raw_complexity))

            # Update archetype string based on seasonal terms selected
            if sum(seasonal_order[:3]) > 0:
                self.archetype = (
                    "The Seasonal Autoregressive Pattern "
                    "(Seasonality + Past Correlation)"
                )
            else:
                self.archetype = "The Autoregressive Pattern (Correlation with Past)"

            return calculate_metrics(val[self.target_col], self.validation_predictions)

        except Exception as e:
            print(f"LOG: AutoARIMA fit failed: {e}")
            inf_metrics = [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]
            return inf_metrics

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if not self.model:
            raise ValueError("Model must be fitted before predict.")

        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        # Point forecast
        mean_vals = self.model.predict(n_periods=horizon)
        if hasattr(mean_vals, "values"):
            mean_vals = mean_vals.values

        # Generate multi-layer confidence intervals using base class logic
        intervals = self._calculate_multi_layer_intervals(mean_vals, self.residuals_std)
        lower, upper = self._calculate_intervals(
            mean_vals, interval_width, self.residuals_std
        )

        df_data = {
            "date": future_dates,
            "mean": mean_vals,
            "median_forecast": mean_vals,
            "lower": lower,
            "upper": upper,
            **intervals,
        }

        if self.freq in ["A", "Y", "AS", "YS"]:
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        model_name = "AutoARIMA"
        if self.model:
            model_name = f"AutoARIMA {self.model.order}{self.model.seasonal_order}"

        return ModelMetadata(
            name=model_name,
            description="Automated selection of ARIMA parameters for optimal fit.",
            rationale=f"Selected due to: {self.archetype}",
            educational_video_url="https://www.youtube.com/watch?v=3UmyHed0iYe",
        )


class RandomForestForecaster(InternalForecaster):
    complexity_score = 5
    archetype = "The Specialist (Sparse Data or Promotions)"

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100, min_samples_leaf=5, random_state=42
        )
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.last_date = None
        self.freq: Optional[str] = None
        self.last_actual_value = 0
        self.last_actual_value = 0
        self.residuals_std = 0.0
        self.last_covariate_values = {}
        self.history_X: Optional[pd.DataFrame] = None

    def _add_features(
        self, df: pd.DataFrame, target: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        X = pd.DataFrame(index=df.index)
        X["month"] = df.index.month
        X["week"] = df.index.isocalendar().week.astype(int)

        for col in df.columns:
            if (
                col != target
                and col != self.time_col
                and pd.api.types.is_numeric_dtype(df[col])
            ):
                X[col] = df[col]

        if target and target in df.columns:
            y = df[target]
            X["lag_1"] = df[target].shift(1).fillna(0)
            return X, y
        else:
            X["lag_1"] = 0
            return X, None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        X, y = self._add_features(df, self.target_col)
        self.last_actual_value = y.iloc[-1]

        self.last_covariate_values = {
            col: X[col].iloc[-1]
            for col in X.columns
            if col not in ["month", "week", "lag_1"]
        }

        split_idx = int(len(X) * 0.8)
        if split_idx == 0:
            split_idx = 1
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_val) == 0:
            # No validation data available; return worst-case metrics so that
            # this model is not incorrectly favored during model selection.
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        X_train = X_train.fillna(0)
        X_val = X_val.fillna(0)

        self.model.fit(X_train, y_train)
        val_preds = self.model.predict(X_val)

        # Calculate residuals for confidence intervals
        residuals = y_val.values - val_preds
        self.residuals_std = float(np.std(residuals)) if len(residuals) > 1 else 0.0
        self.validation_predictions = pd.Series(val_preds, index=y_val.index)
        self.validation_actuals = y_val

        self.model.fit(X.fillna(0), y)

        return calculate_metrics(y_val, self.validation_predictions)

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        overrides = ontology.scenario_overrides if ontology else {}
        model_features = getattr(self.model, "feature_names_in_", [])

        # Build covariate type map for frugal forecasting
        covariate_strategy_map = {}
        if ontology:
            for col_def in ontology.columns:
                if col_def.role == "covariate":
                    if col_def.covariate_strategy:
                        covariate_strategy_map[col_def.column_name] = (
                            col_def.covariate_strategy
                        )
                    # Fallback mapping if strategy not explicitly set
                    elif col_def.covariate_type == "exogenous":
                        covariate_strategy_map[col_def.column_name] = "seasonal_analog"
                    elif col_def.covariate_type == "controllable":
                        covariate_strategy_map[col_def.column_name] = "status_quo"

        forecast_values = []
        current_lag = self.last_actual_value

        for i, date in enumerate(future_dates):
            row_data = {
                "month": [date.month],
                "week": [int(date.isocalendar().week)],
                "lag_1": [current_lag],
            }

            for feat in model_features:
                if feat in ["month", "week", "lag_1"]:
                    continue

                val = 0.0
                if feat in overrides and overrides[feat] is not None:
                    override_val = overrides[feat]
                    if isinstance(override_val, list):
                        idx = min(i, len(override_val) - 1)
                        val = override_val[idx]
                    else:
                        val = float(override_val)
                elif feat in covariate_strategy_map:
                    strategy = covariate_strategy_map[feat]
                    if (
                        strategy == "seasonal_analog"
                        or strategy == "calendar_deterministic"
                    ):
                        # Try 1 year lookback
                        try:
                            # Handle different frequencies if needed, but DateOffset(years=1) is robust
                            target_hist_date = date - pd.DateOffset(years=1)
                            if (
                                self.history_X is not None
                                and target_hist_date in self.history_X.index
                            ):
                                val = self.history_X.loc[target_hist_date, feat]
                            else:
                                # Fallback to status quo if history not found
                                val = self.last_covariate_values.get(feat, 0.0)
                        except Exception:
                            val = self.last_covariate_values.get(feat, 0.0)
                    else:
                        val = self.last_covariate_values.get(feat, 0.0)
                elif feat in self.last_covariate_values:
                    val = self.last_covariate_values[feat]

                row_data[feat] = [val]

            step_X = pd.DataFrame(row_data)
            for missing in set(model_features) - set(step_X.columns):
                step_X[missing] = 0
            step_X = step_X[model_features]

            pred = self.model.predict(step_X)[0]
            forecast_values.append(pred)
            current_lag = pred

        predictions = np.array(forecast_values)
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )
        # Multi-layer intervals
        intervals = self._calculate_multi_layer_intervals(
            predictions, self.residuals_std
        )
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )

        df_data = {
            "date": future_dates,
            "mean": predictions,
            "median_forecast": predictions,
            "lower": lower,
            "upper": upper,
            **intervals,
        }

        if self.freq == "A" or self.freq == "Y":
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="Random Forest (Specialist)",
            description="Machine learning model triggered by sparse data or active promotions.",
            rationale="Selected because data is sparse or contains external drivers.",
            educational_video_url="https://www.youtube.com/watch?v=J4Wdy0Wc_xQ",
        )


class XGBoostForecaster(InternalForecaster):
    complexity_score = 6
    archetype = "The Gradient Specialist (Interactive Drivers & Volatility)"

    def __init__(self):
        self.model = XGBRegressor(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
            verbosity=0,
        )
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.last_date = None
        self.freq: Optional[str] = None
        self.last_actual_value = 0
        self.residuals_std = 0.0
        self.last_actual_value = 0
        self.residuals_std = 0.0
        self.last_covariate_values = {}
        self.history_X: Optional[pd.DataFrame] = None

    def _add_features(
        self, df: pd.DataFrame, target: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        X = pd.DataFrame(index=df.index)
        X["month"] = df.index.month
        X["week"] = df.index.isocalendar().week.astype(int)

        for col in df.columns:
            if (
                col != target
                and col != self.time_col
                and pd.api.types.is_numeric_dtype(df[col])
            ):
                X[col] = df[col]

        if target and target in df.columns:
            y = df[target]
            X["lag_1"] = df[target].shift(1).fillna(0)
            return X, y
        else:
            X["lag_1"] = 0
            return X, None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        X, y = self._add_features(df, self.target_col)
        self.last_actual_value = y.iloc[-1]

        self.last_covariate_values = {
            col: X[col].iloc[-1]
            for col in X.columns
            if col not in ["month", "week", "lag_1"]
        }
        self.history_X = X.copy()

        split_idx = int(len(X) * 0.8)
        if split_idx == 0:
            split_idx = 1
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        if len(X_val) == 0:
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        X_train = X_train.fillna(0)
        X_val = X_val.fillna(0)

        self.model.fit(X_train, y_train)
        val_preds = self.model.predict(X_val)

        residuals = y_val.values - val_preds
        self.residuals_std = float(np.std(residuals)) if len(residuals) > 1 else 0.0
        self.validation_predictions = pd.Series(val_preds, index=y_val.index)
        self.validation_actuals = y_val

        self.model.fit(X.fillna(0), y)

        return calculate_metrics(y_val, self.validation_predictions)

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        overrides = ontology.scenario_overrides if ontology else {}
        model_features = getattr(self.model, "feature_names_in_", [])

        covariate_strategy_map = {}
        if ontology:
            for col_def in ontology.columns:
                if col_def.role == "covariate":
                    if col_def.covariate_strategy:
                        covariate_strategy_map[col_def.column_name] = (
                            col_def.covariate_strategy
                        )
                    # Fallback mapping if strategy not explicitly set
                    elif col_def.covariate_type == "exogenous":
                        covariate_strategy_map[col_def.column_name] = "seasonal_analog"
                    elif col_def.covariate_type == "controllable":
                        covariate_strategy_map[col_def.column_name] = "status_quo"

        forecast_values = []
        current_lag = self.last_actual_value

        for i, date in enumerate(future_dates):
            row_data = {
                "month": [date.month],
                "week": [int(date.isocalendar().week)],
                "lag_1": [current_lag],
            }

            for feat in model_features:
                if feat in ["month", "week", "lag_1"]:
                    continue

                val = 0.0
                if feat in overrides and overrides[feat] is not None:
                    override_val = overrides[feat]
                    if isinstance(override_val, list):
                        idx = min(i, len(override_val) - 1)
                        val = override_val[idx]
                    else:
                        val = float(override_val)
                elif feat in covariate_strategy_map:
                    strategy = covariate_strategy_map[feat]
                    if (
                        strategy == "seasonal_analog"
                        or strategy == "calendar_deterministic"
                    ):
                        # Try 1 year lookback
                        try:
                            # Handle different frequencies if needed, but DateOffset(years=1) is robust
                            target_hist_date = date - pd.DateOffset(years=1)
                            if (
                                self.history_X is not None
                                and target_hist_date in self.history_X.index
                            ):
                                val = self.history_X.loc[target_hist_date, feat]
                            else:
                                # Fallback to status quo if history not found
                                val = self.last_covariate_values.get(feat, 0.0)
                        except Exception:
                            val = self.last_covariate_values.get(feat, 0.0)
                    else:
                        val = self.last_covariate_values.get(feat, 0.0)
                elif feat in self.last_covariate_values:
                    val = self.last_covariate_values[feat]

                row_data[feat] = [val]

            step_X = pd.DataFrame(row_data)
            for missing in set(model_features) - set(step_X.columns):
                step_X[missing] = 0
            step_X = step_X[model_features]

            pred = self.model.predict(step_X)[0]
            forecast_values.append(pred)
            current_lag = pred

        predictions = np.array(forecast_values)
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )
        # Multi-layer intervals
        intervals = self._calculate_multi_layer_intervals(
            predictions, self.residuals_std
        )
        lower, upper = self._calculate_intervals(
            predictions, interval_width, self.residuals_std
        )

        df_data = {
            "date": future_dates,
            "mean": predictions,
            "median_forecast": predictions,
            "lower": lower,
            "upper": upper,
            **intervals,
        }

        if self.freq == "A" or self.freq == "Y":
            df_data["year"] = [d.year for d in future_dates]

        return pd.DataFrame(df_data)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="XGBoost (Specialist)",
            description=(
                "Gradient boosted trees for non-linear interactions "
                "and external drivers."
            ),
            rationale=(
                "Selected for its ability to handle complex covariate interactions."
            ),
            educational_video_url="",
        )


class SmartForecastEngine:
    """
    The Frugal Tournament Engine.
    Runs strictly the defined candidates and selects the 'Frugal Winner'
    based on error metrics and Occam's Razor (Complexity Score).
    """

    def __init__(self):
        self.active_model: Optional[InternalForecaster] = None
        self.tournament_results: List[Dict] = []
        self.data_health_report: Dict[str, Any] = {}

    def select_model(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> List[ForecastMetric]:
        """
        Runs the Tournament.
        """
        print("LOG: Starting Frugal Forecast Tournament...")

        # 1. Define Candidates
        candidates: List[InternalForecaster] = [
            NaiveForecaster(),  # Score 0
            SeasonalNaiveForecaster(),  # Score 0.5
            # ETS Variants (~8)
            ETSForecaster("SES", trend=None, seasonal=None),  # Score 1
            ETSForecaster("Holt Linear", trend="add", seasonal=None),  # Score 2
            ETSForecaster("Holt Multiplicative", trend="mul", seasonal=None),  # Score 2
            ETSForecaster(
                "Damped Additive", trend="add", damped=True, seasonal=None
            ),  # Score 3
            ETSForecaster(
                "Damped Multiplicative", trend="mul", damped=True, seasonal=None
            ),  # Score 3
            ETSForecaster(
                "Holt-Winters Additive", trend="add", seasonal="add"
            ),  # Score 4
            ETSForecaster(
                "Holt-Winters Multiplicative", trend="mul", seasonal="mul"
            ),  # Score 4
            ETSForecaster(
                "Holt-Winters Damped Additive", trend="add", damped=True, seasonal="add"
            ),  # Score 4
            ETSForecaster(
                "Holt-Winters Damped Multiplicative",
                trend="mul",
                damped=True,
                seasonal="mul",
            ),  # Score 4
            # ARIMA Candidate
            ARIMAForecaster(),  # Automated via pmdarima
        ]

        # 2. Check Triggers for Specialist (Random Forest - Score 5)
        target_col_def = next(c for c in ontology.columns if c.role == "target")
        sparsity = 0.0
        if target_col_def.constraints and hasattr(
            target_col_def.constraints, "sparsity_ratio"
        ):
            sparsity = target_col_def.constraints.sparsity_ratio or 0.0

        covariates_present = False
        time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        target_col = next(c.column_name for c in ontology.columns if c.role == "target")

        if (
            len(
                [
                    c
                    for c in df.columns
                    if c not in [time_col, target_col]
                    and pd.api.types.is_numeric_dtype(df[c])
                ]
            )
            > 0
        ):
            covariates_present = True

        if sparsity > 0.5 or covariates_present:
            print("LOG: ML Specialists Triggered. Adding Random Forest & XGBoost.")
            candidates.append(RandomForestForecaster())
            candidates.append(XGBoostForecaster())

        # 3. Run Tournament
        results = []

        for model in candidates:
            try:
                metrics = model.fit(df, ontology)
                mae = next((m.value for m in metrics if m.name == "MAE"), float("inf"))
                mse = next((m.value for m in metrics if m.name == "MSE"), None)
                # Derive MSE from RMSE (calculate_metrics always emits RMSE, never MSE)
                if mse is None:
                    rmse_val = next(
                        (m.value for m in metrics if m.name == "RMSE"), None
                    )
                    mse = (
                        rmse_val**2
                        if (rmse_val is not None and np.isfinite(rmse_val))
                        else float("inf")
                    )

                results.append(
                    {
                        "model": model,
                        "mae": mae,
                        "mse": mse,
                        "complexity": model.complexity_score,
                        "metrics": metrics,
                    }
                )
                print(
                    f"LOG: {model.get_metadata().name} finished. MAE={mae:.4f}, MSE={mse:.4f}, Score={model.complexity_score}"
                )
            except Exception as e:
                print(f"LOG: {model.get_metadata().name} failed/crashed: {e}")

        # 4. Selection Logic (The Rashomon Set)
        valid_results = [r for r in results if np.isfinite(r["mae"]) and r["mae"] > 0.0]
        if not valid_results:
            raise ValueError("All models failed to fit.")

        valid_results.sort(key=lambda x: x["mae"])
        best_mae = valid_results[0]["mae"]

        # Tolerance: 5%
        TOLERANCE = 1.05
        rashomon_set = [r for r in valid_results if r["mae"] <= best_mae * TOLERANCE]

        # Pick the one with Lowest Complexity Score
        rashomon_set.sort(key=lambda x: x["complexity"])
        winner = rashomon_set[0]

        print(
            f"LOG: Winner Selected: {winner['model'].get_metadata().name} (MAE={winner['mae']:.4f}, Complexity={winner['complexity']})"
        )
        if winner["model"] != valid_results[0]["model"]:
            print(
                f"LOG: (Original Best was {valid_results[0]['model'].get_metadata().name} with MAE={valid_results[0]['mae']:.4f} but was rejected due to complexity)"
            )

        self.active_model = winner["model"]
        self.tournament_results = valid_results  # Store for FSS calculation
        return winner["metrics"]

    def _calculate_fss(self) -> Dict[str, Any]:
        """
        Forecast Skill Score (FSS) — a mathematically pure, out-of-sample R²
        metric relative to the Naive baseline.

        FSS = max(0, 1 - MSE_winner / MSE_naive) × 100

        Edge cases:
          - MSE_naive == 0  →  perfect naive forecast, data is a flat line → 100
          - MSE_winner >= MSE_naive  →  max(0, ...) clamps to 0
        """
        if not self.tournament_results or not self.active_model:
            return {
                "score": 0,
                "rating": "Unknown",
                "explanation": "No tournament results available.",
            }

        naive_result = next(
            (
                r
                for r in self.tournament_results
                if isinstance(r["model"], NaiveForecaster)
            ),
            None,
        )
        winner_result = next(
            (r for r in self.tournament_results if r["model"] == self.active_model),
            None,
        )

        if not naive_result or not winner_result:
            return {
                "score": 0,
                "rating": "Unknown",
                "explanation": "Could not compare models.",
            }

        mse_naive = naive_result.get("mse", float("inf"))
        mse_winner = winner_result.get("mse", float("inf"))
        winner_name = self.active_model.get_metadata().name
        winner_complexity = winner_result["complexity"]

        # RMSE is already computed inside calculate_metrics() as sqrt(MSE).
        # Derive it here from the stored MSE to avoid redundant computation.
        rmse_naive = (
            float(np.sqrt(mse_naive)) if np.isfinite(mse_naive) else float("inf")
        )
        rmse_winner = (
            float(np.sqrt(mse_winner)) if np.isfinite(mse_winner) else float("inf")
        )

        print(
            f"LOG: FSS Calculation — RMSE_naive={rmse_naive:.4f}, RMSE_winner={rmse_winner:.4f}"
        )

        # Edge case: perfect naive (data is truly flat)
        if mse_naive < 1e-10:
            fss = 100
        else:
            raw = 1.0 - (mse_winner / mse_naive)
            fss = int(round(max(0.0, raw) * 100))

        # Derive rating from score
        if fss >= 70:
            rating = "High"
        elif fss >= 40:
            rating = "Medium"
        elif fss > 0:
            rating = "Low"
        else:
            rating = "Low (Random)"

        # Build explanation
        if fss == 0:
            explanation = (
                f"The best model ({winner_name}) could not beat the naive baseline on "
                f"the held-out validation set (RMSE_winner={rmse_winner:.4f} \u2265 "
                f"RMSE_naive={rmse_naive:.4f}). "
                f"This score of 0 indicates the data is functionally random or highly "
                f"chaotic to standard models, resulting in a baseline forecast."
            )
        elif fss == 100:
            explanation = (
                f"Perfect forecastability: the naive baseline has zero error, "
                f"meaning the series is a flat line. {winner_name} confirms this."
            )
        else:
            explanation = (
                f"{winner_name} reduces error by {fss}% compared to the naive baseline "
                f"(RMSE_naive={rmse_naive:.4f} \u2192 RMSE_winner={rmse_winner:.4f}). "
                f"The higher this score, the more predictable structure exists in your data."
            )

        return {
            "score": fss,
            "rating": rating,
            "explanation": explanation,
            "mse_naive": round(float(mse_naive), 6),
            "mse_winner": round(float(mse_winner), 6),
            "rmse_naive": round(rmse_naive, 4),
            "rmse_winner": round(rmse_winner, 4),
            "winner_name": winner_name,
            "winner_complexity": winner_complexity,
        }

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        if ontology.ignored_columns:
            drop_cols = [c for c in ontology.ignored_columns if c in df.columns]
            if drop_cols:
                df = df.drop(columns=drop_cols)
            ontology.columns = [
                c
                for c in ontology.columns
                if c.column_name not in ontology.ignored_columns
            ]

        # Always run the tournament for each forecast
        metrics = self.select_model(df, ontology)

        # Calculate FSS after tournament
        self.data_health_report = self._calculate_fss()

        return metrics

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if not self.active_model:
            raise ValueError("Model not fitted yet.")
        return self.active_model.predict(horizon, ontology, interval_width)

    def get_metadata(self) -> Any:
        if not self.active_model:
            return NaiveForecaster().get_metadata()
        return self.active_model.get_metadata()

    def get_backtest_data(self) -> List[Dict[str, Any]]:
        """Returns comparison data for the validation period."""
        if not self.active_model or self.active_model.validation_predictions is None:
            return []

        preds = self.active_model.validation_predictions
        actuals = self.active_model.validation_actuals

        if actuals is None:
            return []

        # Merge onto the same dates
        combined = pd.DataFrame(
            {"date": preds.index, "prediction": preds.values, "actual": actuals.values}
        ).fillna(0)

        import json

        return json.loads(combined.to_json(orient="records", date_format="iso"))

    def get_tournament_results(self) -> List[Dict[str, Any]]:
        """Returns summarized results of all candidates."""
        if not self.tournament_results or not self.active_model:
            return []

        winner_mae = next(
            (
                r["mae"]
                for r in self.tournament_results
                if r["model"] == self.active_model
            ),
            float("inf"),
        )
        TOLERANCE = 1.05

        results = []
        for r in self.tournament_results:
            model = r["model"]
            mae = r["mae"]
            status = "rejected"
            if model == self.active_model:
                status = "winner"
            elif mae <= winner_mae * TOLERANCE:
                status = "runner_up"

            # Read RMSE directly from the stored ForecastMetric objects —
            # calculate_metrics() always emits RMSE; reading it here avoids the
            # brittle mse→sqrt round-trip that was producing float('inf').
            rmse_val = next(
                (float(m.value) for m in r["metrics"] if m.name == "RMSE"),
                None,
            )
            # Derive MSE from RMSE (MSE = RMSE²) for the FSS tooltip display.
            mse_val = (
                round(rmse_val**2, 6)
                if (rmse_val is not None and np.isfinite(rmse_val))
                else None
            )

            row: Dict[str, Any] = {
                "model_name": model.get_metadata().name,
                "mae": mae,
                "complexity": model.complexity_score,
                "status": status,
                "metrics": [m.model_dump() for m in r["metrics"]],
            }
            if rmse_val is not None and np.isfinite(rmse_val):
                row["rmse"] = round(rmse_val, 4)
            if mse_val is not None:
                row["mse"] = mse_val
            results.append(row)
        return results
