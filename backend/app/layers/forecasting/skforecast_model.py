from typing import List, Optional

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from skforecast.direct import ForecasterDirect
from skforecast.preprocessing import RollingFeatures, create_datetime_features

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata
from app.layers.forecasting.base import (
    InternalForecaster,
    calculate_metrics,
    walk_forward_backtest,
)


class SkforecastForecaster(InternalForecaster):
    complexity_score = 7
    archetype = "The Direct Strategist (Zero-Leakage ML)"
    supports_covariates = True

    def __init__(self, regressor_type="lightgbm"):
        self.regressor_type = regressor_type
        if regressor_type == "lightgbm":
            self.regressor = LGBMRegressor(
                random_state=42, n_estimators=100, verbose=-1, n_jobs=1
            )
            self.complexity_score = 7
        elif regressor_type == "xgboost":
            from xgboost import XGBRegressor

            # n_jobs=1 is critical on Windows to prevent Access Violations in multiprocess workers
            self.regressor = XGBRegressor(
                random_state=42, n_estimators=100, verbosity=0, n_jobs=1
            )
            self.complexity_score = 6
        else:  # rf
            from sklearn.ensemble import RandomForestRegressor

            self.regressor = RandomForestRegressor(
                random_state=42, n_estimators=100, n_jobs=1
            )
            self.complexity_score = 5

        self.forecaster = None
        self.time_col = None
        self.target_col = None
        self.known_cols = []
        self.unknown_cols = []
        self.engineered_unknown_cols = []
        self.internal_feature_cols = []
        self.lag_window = 7
        self.last_date = None
        self.freq = None
        self.history_df = None
        self._original_unknown = {}
        self.residuals_std = 0.0

    def prep_forecasting_data(
        self,
        df: pd.DataFrame,
        target_col: str,
        known_cols: List[str],
        unknown_cols: List[str],
    ):
        # 1. KNOWN FUTURES: Leave these exactly as they are.
        df_processed = df[[target_col] + known_cols].copy()

        # 2. CALENDAR FEATURES: Native skforecast datetime features (no leakage)
        calendar_df = create_datetime_features(
            df_processed,
            features=["month", "day_of_week", "weekend", "day_of_year"],
            encoding=None,
        )
        calendar_df = calendar_df.add_prefix("skf_")
        internal_cols = list(calendar_df.columns)
        df_processed = pd.concat([df_processed, calendar_df], axis=1)

        # 3. UNKNOWN PASTS: Mathematically prevent leakage by shifting them.
        engineered_unknown = []
        for col in unknown_cols:
            for lag in range(1, self.lag_window + 1):
                lag_name = f"{col}_lag_{lag}"
                df_processed[lag_name] = df[col].shift(lag)
                engineered_unknown.append(lag_name)

        # Drop rows with NaNs caused by the lagging process
        df_processed = df_processed.dropna()
        return df_processed, engineered_unknown, internal_cols

    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        self.time_col = next(
            c.column_name for c in ontology.columns if c.role == "time_index"
        )
        self.target_col = next(
            c.column_name for c in ontology.columns if c.role == "target"
        )

        # Identify buckets - ensuring we only take numeric columns for now to prevent model crashes
        # (categorical encoding could be added here in the future)
        self.known_cols = [
            c.column_name
            for c in ontology.columns
            if c.role == "covariate"
            and c.covariate_type == "known_future"
            and pd.api.types.is_numeric_dtype(df[c.column_name])
        ]
        self.unknown_cols = [
            c.column_name
            for c in ontology.columns
            if c.role == "covariate"
            and c.covariate_type == "unknown_past"
            and pd.api.types.is_numeric_dtype(df[c.column_name])
        ]

        # Set index
        df = df.copy()
        df[self.time_col] = pd.to_datetime(df[self.time_col])
        df = df.set_index(self.time_col)
        self.freq = pd.infer_freq(df.index) or "D"
        df.index.freq = self.freq  # Crucial for skforecast
        self.last_date = df.index.max()

        # Prep data
        df_processed, self.engineered_unknown_cols, self.internal_feature_cols = (
            self.prep_forecasting_data(
                df, self.target_col, self.known_cols, self.unknown_cols
            )
        )
        # pd.concat strips freq attribute, and dropna() doesn't restore it.
        df_processed = df_processed.asfreq(self.freq)

        # Safety check: if lagging killed too many rows
        if len(df_processed) < 10:
            print(
                f"LOG: Skforecast skipped - only {len(df_processed)} rows left after lagging."
            )
            return [ForecastMetric(name="MAE", value=float("inf"))]

        self.history_df = df_processed.copy()
        self._original_unknown = {
            col: df[col].values.copy() for col in self.unknown_cols
        }

        all_exog_features = (
            self.known_cols + self.engineered_unknown_cols + self.internal_feature_cols
        )
        horizon_steps = ontology.requirements.horizon_requirement.steps

        def _choose_lags_and_windows(budget: int):
            """Return (lags, window_features) given training budget."""
            if budget >= 28:
                return 14, RollingFeatures(stats=["mean", "std"], window_sizes=[7, 14])
            elif budget >= 21:
                return 14, RollingFeatures(stats=["mean", "std"], window_sizes=[7, 7])
            elif budget >= 14:
                return 7, RollingFeatures(stats=["mean"], window_sizes=[7])
            elif budget >= 7:
                return 7, None
            else:
                return max(1, budget), None

        def _fit_predict(train_df: pd.DataFrame, val_df: pd.DataFrame) -> pd.Series:
            budget = len(train_df) - horizon_steps
            if budget < 1:
                # Not enough train budget for this window — fallback to naive
                return pd.Series(
                    [train_df[self.target_col].iloc[-1]] * len(val_df),
                    index=val_df.index,
                )
            lags, window_features = _choose_lags_and_windows(budget)
            forecaster = ForecasterDirect(
                estimator=self.regressor,
                steps=horizon_steps,
                lags=lags,
                window_features=window_features,
                n_jobs=1,
            )
            forecaster.fit(
                y=train_df[self.target_col],
                exog=train_df[all_exog_features] if all_exog_features else None,
            )
            chunk_steps = len(val_df)
            preds = forecaster.predict(
                steps=chunk_steps,
                exog=val_df[all_exog_features] if all_exog_features else None,
            )
            return pd.Series(preds.values, index=val_df.index)

        try:
            val_preds, val_actuals = walk_forward_backtest(
                df_processed,
                self.time_col,
                self.target_col,
                horizon_steps=horizon_steps,
                fit_predict_fn=_fit_predict,
            )

            if len(val_preds) == 0:
                return [ForecastMetric(name="MAE", value=float("inf"))]

            self.validation_predictions = val_preds
            self.validation_actuals = val_actuals
            metrics = calculate_metrics(val_actuals, val_preds)
            self.residuals_std = float(np.std(val_actuals.values - val_preds.values))
        except Exception as e:
            print(f"LOG: Skforecast backtest failed: {e}")
            return [ForecastMetric(name="MAE", value=float("inf"))]

        # Final fit on 100% processed data
        full_budget = len(df_processed) - horizon_steps
        if full_budget < 1:
            return [ForecastMetric(name="MAE", value=float("inf"))]
        final_lags, final_window_features = _choose_lags_and_windows(full_budget)

        self.forecaster = ForecasterDirect(
            estimator=self.regressor,
            steps=horizon_steps,
            lags=final_lags,
            window_features=final_window_features,
            n_jobs=1,
        )
        self.forecaster.fit(
            y=df_processed[self.target_col],
            exog=df_processed[all_exog_features] if all_exog_features else None,
        )

        return metrics

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        if not self.forecaster:
            raise ValueError("Model not fitted.")

        # 1. Prepare Future Exog
        # Known Future: from overrides
        overrides_list = ontology.scenario_overrides or [] if ontology else []
        overrides = (
            {o.column_name: o.values for o in overrides_list}
            if isinstance(overrides_list, list)
            else {}
        )
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]

        future_exog_known = pd.DataFrame(index=future_dates)
        for col in self.known_cols:
            val = overrides.get(col)
            if isinstance(val, list):
                # Use provided series
                future_exog_known[col] = (val + [val[-1]] * horizon)[:horizon]
            elif val == "seasonal":
                future_exog_known[col] = self._get_seasonal_future_values(col, horizon)
            elif val is not None:
                future_exog_known[col] = float(val)
            else:
                # Status quo: use last historical value
                future_exog_known[col] = self.history_df[col].iloc[-1]

        # Unknown Past: Build lag features from future values
        future_exog_unknown = self._build_future_exog_unknown(
            horizon, future_dates, overrides
        )

        final_future_exog = pd.concat([future_exog_known, future_exog_unknown], axis=1)

        # Add calendar features for future dates
        if self.internal_feature_cols:
            future_calendar = create_datetime_features(
                pd.DataFrame(index=future_dates),
                features=["month", "day_of_week", "weekend", "day_of_year"],
                encoding=None,
            )
            future_calendar = future_calendar.add_prefix("skf_")
            final_future_exog = pd.concat([final_future_exog, future_calendar], axis=1)

        all_features = (
            self.known_cols + self.engineered_unknown_cols + self.internal_feature_cols
        )
        final_future_exog = final_future_exog[all_features] if all_features else None

        # 2. Predict
        # skforecast predict
        preds = self.forecaster.predict(steps=horizon, exog=final_future_exog)

        # 3. Intervals (Simple Normal approximation for now as skforecast intervals vary by regressor)
        z = 1.28 if interval_width == 0.80 else 1.96
        lower = preds - (z * self.residuals_std)
        upper = preds + (z * self.residuals_std)

        # Multi-layer intervals for premium UI
        intervals = self._calculate_multi_layer_intervals(
            preds.values, self.residuals_std
        )

        return pd.DataFrame(
            {
                "date": future_dates,
                "mean": preds.values,
                "median_forecast": preds.values,
                "lower": lower.values,
                "upper": upper.values,
                **intervals,
            }
        )

    def _get_seasonal_future_values(self, col: str, horizon: int) -> np.ndarray:
        """Get seasonal analog values for a future horizon."""
        history = self._original_unknown.get(col, np.array([]))
        period_map = {"D": 7, "W": 52, "M": 12, "Q": 4, "Y": 1, "H": 24}
        period = period_map.get(self.freq, None)
        if period is None or len(history) < period:
            last_val = float(history[-1]) if len(history) > 0 else 0.0
            return np.full(horizon, last_val, dtype=float)
        values = []
        for i in range(horizon):
            idx = len(history) + i - period
            while idx >= len(history):
                idx -= period
            if idx >= 0:
                values.append(float(history[idx]))
            else:
                values.append(float(history[-1]) if len(history) > 0 else 0.0)
        return np.array(values, dtype=float)

    def _get_steady_future_values(self, col: str, horizon: int) -> np.ndarray:
        """Get hold-steady future values (last known value repeated)."""
        history = self._original_unknown.get(col, np.array([]))
        last_val = float(history[-1]) if len(history) > 0 else 0.0
        return np.full(horizon, last_val, dtype=float)

    def _build_future_lag_features(
        self, col: str, future_values: np.ndarray, future_dates: pd.DatetimeIndex
    ) -> pd.DataFrame:
        """Build lag features for an unknown column for the future period."""
        history = self._original_unknown.get(col, np.array([]))
        combined = np.concatenate([history, future_values])
        lag_features = {}
        for lag in range(1, self.lag_window + 1):
            lag_name = f"{col}_lag_{lag}"
            values = []
            for i in range(len(future_values)):
                idx = len(history) + i - lag
                if idx >= 0:
                    values.append(float(combined[idx]))
                else:
                    values.append(float(history[0]) if len(history) > 0 else 0.0)
            lag_features[lag_name] = values
        return pd.DataFrame(lag_features, index=future_dates)

    def _build_future_exog_unknown(
        self, horizon: int, future_dates: pd.DatetimeIndex, overrides: dict
    ) -> pd.DataFrame:
        """Build future exogenous features for unknown covariates."""
        future_exog_unknown = pd.DataFrame(index=future_dates)
        for col in self.unknown_cols:
            strategy = overrides.get(col)
            if strategy == "seasonal":
                future_values = self._get_seasonal_future_values(col, horizon)
            elif isinstance(strategy, list):
                padded = (strategy + [strategy[-1]] * horizon)[:horizon]
                future_values = np.array(padded, dtype=float)
            elif isinstance(strategy, (int, float)):
                future_values = np.full(horizon, float(strategy), dtype=float)
            else:
                future_values = self._get_steady_future_values(col, horizon)
            col_lag_df = self._build_future_lag_features(
                col, future_values, future_dates
            )
            future_exog_unknown = pd.concat([future_exog_unknown, col_lag_df], axis=1)
        return future_exog_unknown

    def get_metadata(self) -> ModelMetadata:
        reg_name = (
            self.regressor_type.upper()
            if self.regressor_type != "rf"
            else "Random Forest"
        )
        if reg_name == "LIGHTGBM":
            reg_name = "LightGBM"
        if reg_name == "XGBOOST":
            reg_name = "XGBoost"

        # Build feature engineering report from instance state
        fe_steps = []
        if self.internal_feature_cols:
            fe_steps.append(
                f"Calendar features: {', '.join(self.internal_feature_cols)}"
            )
        if self.forecaster and getattr(self.forecaster, "window_features", None):
            for wf in self.forecaster.window_features:
                fe_steps.append(
                    f"Rolling window features: {', '.join(wf.features_names)}"
                )
        if self.engineered_unknown_cols:
            fe_steps.append(
                f"Covariate lag features: {', '.join(self.engineered_unknown_cols)}"
            )

        return ModelMetadata(
            name=reg_name,
            description="A machine learning approach that learns complex patterns from your historical data and any supporting factors.",
            rationale="Mathematically rigorous handling of known vs unknown drivers with high-capacity ML.",
            educational_video_url="",
            feature_engineering_steps=fe_steps if fe_steps else None,
        )
