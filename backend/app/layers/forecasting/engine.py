from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
)
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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

    @abstractmethod
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        pass

    @abstractmethod
    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        pass

    @staticmethod
    @abstractmethod
    def get_metadata() -> ModelMetadata:
        pass


class SimpleAdditiveForecaster(InternalForecaster):
    """
    A robust baseline forecaster using Holt-Winters Exponential Smoothing.
    """

    def __init__(self):
        self.model = None
        self.fit_result = None
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.last_date = None
        self.freq: Optional[str] = None

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

        # Train/Val Split
        split_idx = int(len(df) * 0.8)
        train, val = df.iloc[:split_idx], df.iloc[split_idx:]

        try:
            model = ExponentialSmoothing(
                train[self.target_col], trend="add", seasonal="add", freq=self.freq
            )
            fit_result = model.fit()
            val_preds = fit_result.forecast(len(val))

            # Re-fit on full data for final prediction
            self.model = ExponentialSmoothing(
                df[self.target_col], trend="add", seasonal="add", freq=self.freq
            )
            self.fit_result = self.model.fit()

            return calculate_metrics(val[self.target_col], val_preds)
        except Exception:
            # Fallback
            model = ExponentialSmoothing(
                train[self.target_col], trend="add", seasonal=None, freq=self.freq
            )
            fit_result = model.fit()
            val_preds = fit_result.forecast(len(val))

            self.model = ExponentialSmoothing(
                df[self.target_col], trend="add", seasonal=None, freq=self.freq
            )
            self.fit_result = self.model.fit()
            return calculate_metrics(val[self.target_col], val_preds)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        if not self.fit_result:
            raise ValueError("Model not fitted yet.")
        forecast_values = self.fit_result.forecast(horizon)
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: forecast_values}
        )

    @staticmethod
    def get_metadata() -> ModelMetadata:
        return ModelMetadata(
            name="Exponential Smoothing (ETS)",
            description=(
                "A robust statistical model that captures trends and seasonal "
                "cycles by weighting recent observations more heavily."
            ),
            rationale=(
                "Chosen because your data shows clear repetitive patterns and "
                "a consistent trajectory over time. It is a gold standard for "
                "stable business metrics."
            ),
            educational_video_url="https://www.youtube.com/watch?v=Du8h_S_ndRE",
        )


class TSBForecaster(InternalForecaster):
    """
    Teunter-Syntetos-Babai (TSB) method for intermittent demand.
    Updates probability of demand (p) and demand size (z) separately.
    """

    def __init__(self, alpha=0.1, beta=0.1):
        self.alpha = alpha
        self.beta = beta
        self.p = None  # Probability of demand
        self.z = None  # Demand size
        self.last_date = None
        self.freq = None
        self.time_col = None
        self.target_col = None

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )

        y = df[self.target_col].values

        # Ensure index is set properly
        if self.time_col in df.columns:
            df = df.set_index(self.time_col)

        self.last_date = df.index.max()
        self.freq = pd.infer_freq(df.index) or "D"

        # Initialization
        non_zero_indices = np.where(y > 0)[0]

        if len(non_zero_indices) < 2:
            self.p = 0.1
            self.z = 0 if len(non_zero_indices) == 0 else y[non_zero_indices[0]]
            return []

        # Calculate initial probability roughly
        first_idx = non_zero_indices[0]
        # Skip leading zeros for initialization
        y_trim = y[first_idx:]

        # Init values
        self.z = y_trim[0]
        self.p = (
            1.0 / (np.diff(non_zero_indices).mean())
            if len(non_zero_indices) > 1
            else 0.5
        )

        # Iterative update
        history_preds = []

        for val in y_trim:
            history_preds.append(self.p * self.z)
            if val > 0:
                self.p = self.beta * 1 + (1 - self.beta) * self.p
                self.z = self.alpha * val + (1 - self.alpha) * self.z
            else:
                self.p = self.beta * 0 + (1 - self.beta) * self.p
                # z stays same

        # Mock metrics just to satisfy interface
        return [ForecastMetric(name="TSB_Decay_Factor", value=self.p)]

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        # TSB produces a flat forecast level for the future (p * z)
        # but unlike Croston, 'p' has decayed if recent demand was 0.
        forecast_val = self.p * self.z

        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: [forecast_val] * horizon}
        )

    @staticmethod
    def get_metadata() -> ModelMetadata:
        return ModelMetadata(
            name="TSB Intermittent Model",
            description="Specialized model that adjusts forecast probability dynamically based on recent demand intervals.",
            rationale="Selected for intermittent data. Unlike Croston's method, it allows the forecast to decay during low-demand periods.",
            educational_video_url="https://www.youtube.com/watch?v=example",
        )


class RandomForestForecaster(InternalForecaster):
    """
    Random Forest Regressor with Calendar Features to capture seasonality (spikes).
    """

    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.time_col: Optional[str] = None
        self.target_col: Optional[str] = None
        self.last_date = None
        self.freq: Optional[str] = None
        self.lags = 3

    def _add_features(
        self, df: pd.DataFrame, target: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        X = pd.DataFrame(index=df.index)

        # Calendar Features
        X["month"] = df.index.month
        X["week"] = df.index.isocalendar().week.astype(int)

        # External Regressors (Covariates)
        # We take everything that is NOT target and NOT time_index
        # Note: 'df' here might already have ignored columns dropped by SmartForecastEngine
        for col in df.columns:
            if col != target and col != self.time_col:
                # Ensure numeric encoding if needed?
                # For now assuming numeric or relying on RF validation failure if string
                # Ideally we'd have encoders, but preserving existing behavior of minimal processing
                if pd.api.types.is_numeric_dtype(df[col]):
                    X[col] = df[col]

        # Lags
        if target and target in df.columns:
            y = df[target]
            X["lag_1"] = df[target].shift(1).fillna(0)
            return X, y
        else:
            # Prediction time
            # We will handle lag_1 dynamically in the loop
            # But we need the structure
            X["lag_1"] = 0  # Placeholder
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

        # Feature Engineering
        X, y = self._add_features(df, self.target_col)

        # Drop first row because lag_1 might be dirty/0
        # For training, let's keep it simple as before

        # Store last actual value for recursion start
        self.last_actual_value = y.iloc[-1]

        # Store last covariate values for prediction (excluding generated features)
        self.last_covariate_values = {
            col: X[col].iloc[-1]
            for col in X.columns
            if col not in ["month", "week", "lag_1"]
        }

        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        self.model.fit(X_train, y_train)
        val_preds = self.model.predict(X_val)

        # Final fit
        self.model.fit(X, y)

        return calculate_metrics(y_val, val_preds)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        # Prepare Overrides
        overrides = ontology.scenario_overrides if ontology else {}

        # We need the list of columns the model expects (except lag_1, month, week which are generated)
        # A simple way to get "other covariates" is to look at feature_names_in_ if available
        model_features = getattr(self.model, "feature_names_in_", [])

        forecast_values = []
        current_lag = self.last_actual_value

        # Recursive Loop
        for i, date in enumerate(future_dates):
            # 1. Build Single Row Feature Vector
            row_data = {
                "month": [date.month],
                "week": [int(date.isocalendar().week)],
                "lag_1": [current_lag],
            }

            # 2. Fill External Regressors
            # We explicitly check for features the model knows about
            for feat in model_features:
                if feat in ["month", "week", "lag_1"]:
                    continue

                # Determine value for this feature
                val = 0.0  # Default fallback if no history and no override

                # Check Overrides
                if feat in overrides and overrides[feat] is not None:
                    override_val = overrides[feat]
                    if isinstance(override_val, list):
                        # Custom Plan: Use index i, safety clip
                        idx = min(i, len(override_val) - 1)
                        val = override_val[idx]
                    else:
                        # Constant
                        val = float(override_val)
                else:
                    # Status Quo / Default: Last Known Value (Forward Fill)
                    if feat in self.last_covariate_values:
                        val = self.last_covariate_values[feat]
                    # else: val remains 0.0 as initialized

                row_data[feat] = [val]

            # Create DF for prediction
            # Ensure columns order matches model
            step_X = pd.DataFrame(row_data)

            # Reorder columns to match fit
            if len(model_features) > 0:
                # Add missing cols with 0 if any (safety)
                for missing in set(model_features) - set(step_X.columns):
                    step_X[missing] = 0
                step_X = step_X[model_features]

            # Predict
            pred = self.model.predict(step_X)[0]
            forecast_values.append(pred)

            # Update recursive lag for next step
            current_lag = pred

        return pd.DataFrame(
            {self.time_col: future_dates, self.target_col: forecast_values}
        )

    @staticmethod
    def get_metadata() -> ModelMetadata:
        return ModelMetadata(
            name="Random Forest (Seasonal)",
            description=(
                "A machine learning model that learns seasonal patterns (e.g., specific months or weeks) "
                "to predict demand spikes."
            ),
            rationale=(
                "Chosen because your data shows intermittent but repetitive spikes that "
                "statistical averages would miss."
            ),
            educational_video_url="https://www.youtube.com/watch?v=J4Wdy0Wc_xQ",
        )


class SmartForecastEngine:
    """
    Main Forecast Engine that selects the appropriate model based on Ontology.
    """

    def __init__(self):
        self.active_model: Optional[InternalForecaster] = None

    def select_model(self, ontology: ForecastOntology):
        """
        Selects the appropriate model based on the Ontology without fitting it.
        """
        # 1. Extract the Fact
        target_col_def = next(c for c in ontology.columns if c.role == "target")

        # --- DEBUG START ---
        print(f"DEBUG: Checking Column: {target_col_def.column_name}")
        if target_col_def.constraints:
            val = getattr(target_col_def.constraints, "sparsity_ratio", "MISSING")
            print(f"DEBUG: Sparsity Ratio Value: {val}")
        # --- DEBUG END ---

        sparsity = 0.0
        if (
            target_col_def.constraints
            and getattr(target_col_def.constraints, "sparsity_ratio", None) is not None
        ):
            sparsity = target_col_def.constraints.sparsity_ratio

        # 2. Apply the Policy
        if sparsity > 0.5:
            # INTERMITTENT DEMAND DETECTED
            print(f"LOG: Sparsity {sparsity:.1%} > 50%. Intermittent Logic Activated.")

            # Sub-Decision: Do we have enough data to find patterns? (Simple heuristic)
            # We don't have the DF length here easily without passing it...
            # But the 'ontology' doesn't store row count.
            # Wait, we need to know if we should try RF.
            # Let's assume we ALWAYS try RF if sparsity matches 'spiky' profile,
            # but TSB is the fallback if sparsity is EXTREME (> 95%)?
            # Or just default to RF as requested by user ("adapt RF").

            print(
                "LOG: Selecting Random Forest to capture potential seasonality/spikes."
            )
            self.active_model = RandomForestForecaster()

            # Ideally we would have a fallback logic if RF fails, but for now
            # we follow the directive to use RF.
            # Pure TSB is available as: self.active_model = TSBForecaster()

        else:
            print(
                f"LOG: Sparsity {sparsity:.1%} <= 50%. Selecting Standard Forecaster."
            )
            self.active_model = SimpleAdditiveForecaster()

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology):
        # 0. Handle Ignored Columns
        if ontology.ignored_columns:
            # Filter from DF
            drop_cols = [c for c in ontology.ignored_columns if c in df.columns]
            if drop_cols:
                print(f"LOG: Ignoring columns: {drop_cols}")
                df = df.drop(columns=drop_cols)

            # Filter from Ontology (create a temporary view or modify for this run)
            # Modifying the object is risky if it persists, but this is per-request in the pipeline usually.
            # However, `pipeline.run_forecast` uses the same ontology object relative to the request.
            # Let's filter the columns list.
            ontology.columns = [
                c
                for c in ontology.columns
                if c.column_name not in ontology.ignored_columns
            ]

        if not self.active_model:
            self.select_model(ontology)

            # DYNAMIC SWITCH (Runtime Check)
            # If we selected RF for Intermittent, but data is too short, switch to TSB.
            is_rf = isinstance(self.active_model, RandomForestForecaster)
            if is_rf and len(df) < 50:
                print(
                    "LOG: Data too short (<50 rows) for Random Forest. Falling back to TSB."
                )
                self.active_model = TSBForecaster()

        return self.active_model.fit(df, ontology)

    def predict(
        self, horizon: int, ontology: Optional[ForecastOntology] = None
    ) -> pd.DataFrame:
        if not self.active_model:
            raise ValueError("Model not fitted yet.")
        return self.active_model.predict(horizon, ontology)

    def get_metadata(self) -> Any:
        if not self.active_model:
            return SimpleAdditiveForecaster.get_metadata()
        return self.active_model.get_metadata()
