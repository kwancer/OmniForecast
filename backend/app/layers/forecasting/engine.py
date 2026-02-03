from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA

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

    @abstractmethod
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        pass

    @abstractmethod
    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_metadata(self) -> ModelMetadata:
        pass


class NaiveForecaster(InternalForecaster):
    complexity_score = 0
    archetype = "The Flat Line / Random Walk (Tomorrow = Today)"

    def __init__(self):
        self.last_value = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None

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

        # Final fit
        self.last_value = df[self.target_col].iloc[-1]

        return calculate_metrics(val[self.target_col], val_preds)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: [self.last_value] * horizon}
        )

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

        self.history = df[self.target_col]
        return calculate_metrics(val[self.target_col], val_preds)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        preds = []
        last_season = self.history.iloc[-self.season_length :].values

        for i in range(horizon):
            preds.append(last_season[i % self.season_length])

        return pd.DataFrame({self.time_col: future_dates, self.target_col: preds})

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
                seasonal_periods = 7 if self.freq == 'D' else (12 if self.freq == 'M' else None)
            
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

            return calculate_metrics(val[self.target_col], val_preds)
        except Exception as e:
            print(f"LOG: Model {self.config_name} failed: {e}")
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
            ]

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        if not self.fit_result:
            raise ValueError("Model not fitted.")

        forecast_values = self.fit_result.forecast(horizon)
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: forecast_values}
        )

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=f"ETS ({self.config_name})",
            description=f"Exponential Smoothing: {self.config_name}. {self.archetype}",
            rationale=f"Selected due to {self.archetype} characteristics.",
            educational_video_url="https://www.youtube.com/watch?v=Du8h_S_ndRE",
        )


class ARIMAForecaster(InternalForecaster):
    """
    ARIMA candidate for the tournament.
    """
    def __init__(self, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0)):
        self.order = order
        self.seasonal_order = seasonal_order
        # Complexity scoring heuristic:
        #   - Start from a base complexity of 1.
        #   - Add (sum of ARIMA order + sum of first three seasonal_order terms) / 6.0.
        #   - The 4th seasonal_order term (seasonal period) is intentionally excluded.
        #   - The raw score can be outside [1, 4]; we clamp it afterward for a stable 1–4 scale.
        self.complexity_score = 1 + (sum(order) + sum(seasonal_order[:3])) / 6.0
        # Clamp to the public 1–4 complexity scale
        self.complexity_score = max(1, min(4, self.complexity_score))
        self.archetype = "The Autoregressive Pattern (Correlation with Past)"
        
        self.fit_result = None
        self.time_col = None
        self.target_col = None
        self.last_date = None
        self.freq = None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(c.column_name for c in ontology.columns if c.role == "time_index")
        self.target_col = next(c.column_name for c in ontology.columns if c.role == "target")
        df = df.set_index(self.time_col)
        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        split_idx = int(len(df) * 0.8)
        if split_idx == 0:
            split_idx = 1
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        if len(val) == 0:
            # No validation data available: avoid returning perfect (zero) metrics
            # which would mislead model selection. Use infinite errors instead.
            return [
                ForecastMetric(name="MAE", value=float("inf")),
                ForecastMetric(name="RMSE", value=float("inf")),
                ForecastMetric(name="MAPE", value=float("inf")),
            ]

        try:
            model = ARIMA(train[self.target_col], order=self.order, seasonal_order=self.seasonal_order)
            fit_result = model.fit()
            val_preds = fit_result.forecast(len(val))

            full_model = ARIMA(df[self.target_col], order=self.order, seasonal_order=self.seasonal_order)
            self.fit_result = full_model.fit()

            return calculate_metrics(val[self.target_col], val_preds)
        except Exception as e:
            print(f"LOG: ARIMA {self.order} failed: {e}")
            return [ForecastMetric(name="MAE", value=float("inf"))]

    def predict(self, horizon: int, ontology: Optional[ForecastOntology] = None) -> pd.DataFrame:
        forecast_values = self.fit_result.forecast(horizon)
        future_dates = pd.date_range(start=self.last_date, periods=horizon + 1, freq=self.freq)[1:]
        return pd.DataFrame({self.time_col: future_dates, self.target_col: forecast_values})

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name=f"ARIMA {self.order}",
            description="AutoRegressive Integrated Moving Average model.",
            rationale="Captures autocorrelations in the data.",
            educational_video_url="https://www.youtube.com/watch?v=3UmyHed0iYe"
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

        self.model.fit(X.fillna(0), y)

        return calculate_metrics(y_val, val_preds)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        overrides = ontology.scenario_overrides if ontology else {}
        model_features = getattr(self.model, "feature_names_in_", [])

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

        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: forecast_values}
        )

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            name="Random Forest (Specialist)",
            description="Machine learning model triggered by sparse data or active promotions.",
            rationale="Selected because data is sparse or contains external drivers.",
            educational_video_url="https://www.youtube.com/watch?v=J4Wdy0Wc_xQ",
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
            # ETS Variants (~9)
            ETSForecaster("SES", trend=None, seasonal=None),  # Score 1
            ETSForecaster("Holt Linear", trend="add", seasonal=None),  # Score 2
            ETSForecaster("Holt Multiplicative", trend="mul", seasonal=None),  # Score 2
            ETSForecaster("Damped Additive", trend="add", damped=True, seasonal=None),  # Score 3
            ETSForecaster("Damped Multiplicative", trend="mul", damped=True, seasonal=None),  # Score 3
            ETSForecaster("Holt-Winters Additive", trend="add", seasonal="add"),  # Score 4
            ETSForecaster("Holt-Winters Multiplicative", trend="mul", seasonal="mul"),  # Score 4
            ETSForecaster("Holt-Winters Damped Additive", trend="add", damped=True, seasonal="add"),  # Score 4
            ETSForecaster("Holt-Winters Damped Multiplicative", trend="mul", damped=True, seasonal="mul"),  # Score 4
            # ARIMA Candidate
            ARIMAForecaster(order=(1, 1, 1)), # Score ~1.5
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
            print(
                f"LOG: Specialist Triggered (Sparsity={sparsity:.2f}, Covariates={covariates_present}). Adding Random Forest."
            )
            candidates.append(RandomForestForecaster())

        # 3. Run Tournament
        results = []

        for model in candidates:
            try:
                metrics = model.fit(df, ontology)
                mae = next((m.value for m in metrics if m.name == "MAE"), float("inf"))

                results.append(
                    {
                        "model": model,
                        "mae": mae,
                        "complexity": model.complexity_score,
                        "metrics": metrics,
                    }
                )
                print(
                    f"LOG: {model.get_metadata().name} finished. MAE={mae:.4f}, Score={model.complexity_score}"
                )
            except Exception as e:
                print(f"LOG: {model.get_metadata().name} failed/crashed: {e}")

        # 4. Selection Logic (The Rashomon Set)
        valid_results = [
            r
            for r in results
            if np.isfinite(r["mae"]) and r["mae"] > 0.0
        ]
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
        return winner["metrics"]

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

        if not self.active_model:
            return self.select_model(df, ontology)

        return self.active_model.fit(df, ontology)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        if not self.active_model:
            raise ValueError("Model not fitted yet.")
        return self.active_model.predict(horizon, ontology)

    def get_metadata(self) -> Any:
        if not self.active_model:
            return NaiveForecaster().get_metadata()
        return self.active_model.get_metadata()
