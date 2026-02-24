from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology, ModelMetadata
from app.layers.forecasting.base import InternalForecaster, calculate_metrics


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
        self.last_date: Optional[pd.Timestamp] = None
        self.freq: Optional[str] = None
        self.last_actual_value = 0
        self.residuals_std = 0.0
        self.last_actual_value = 0
        self.residuals_std = 0.0
        self.last_covariate_values = {}
        self.history_X: Optional[pd.DataFrame] = None

    def _add_features(
        self, df: pd.DataFrame, target: Optional[str] = None
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        index = pd.DatetimeIndex(df.index)
        X = pd.DataFrame(index=index)
        X["month"] = index.month
        X["week"] = index.isocalendar().week.astype(int)

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
        df.index = pd.to_datetime(df.index)
        self.last_date = pd.Timestamp(df.index.max())
        self.freq = pd.infer_freq(pd.DatetimeIndex(df.index)) or "D"

        X, y = self._add_features(df, self.target_col)
        if y is None:
            raise ValueError("Target column missing for XGBoost forecaster.")
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
        if self.last_date is None or self.freq is None:
            raise ValueError("Model not fitted.")
        future_dates = pd.date_range(
            start=self.last_date, periods=horizon + 1, freq=self.freq
        )[1:]
        overrides: Dict[str, Any] = (
            ontology.scenario_overrides or {} if ontology else {}
        )
        model_features = getattr(self.model, "feature_names_in_", [])

        covariate_strategy_map: Dict[str, str] = {}
        if ontology:
            for col_def in ontology.columns:
                if col_def.role == "covariate":
                    covariate_strategy = getattr(col_def, "covariate_strategy", None)
                    if covariate_strategy:
                        covariate_strategy_map[col_def.column_name] = covariate_strategy
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
                        val = float(override_val) if override_val is not None else 0.0
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
                        except (KeyError, ValueError, TypeError):
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
