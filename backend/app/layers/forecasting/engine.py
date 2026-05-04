from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from app.domain.data import ForecastMetric
from app.domain.ontology import ForecastOntology
from app.layers.forecasting.arima import ARIMAForecaster
from app.layers.forecasting.base import InternalForecaster
from app.layers.forecasting.ets import ETSForecaster
from app.layers.forecasting.naive import NaiveForecaster
from app.layers.forecasting.seasonal_naive import SeasonalNaiveForecaster
from app.layers.forecasting.skforecast_model import SkforecastForecaster


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
        self.progress_callback: Optional[Callable[[int, int, str], None]] = None

    def set_progress_callback(self, callback: Callable[[int, int, str], None]) -> None:
        """
        Set a callback function to report tournament progress.

        Args:
            callback: Function that takes (current, total, model_name) as arguments
        """
        self.progress_callback = callback

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
            # ARIMAForecaster(),  # Automated via pmdarima (Temporarily disabled)
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

        # Check for covariates in ontology roles or extra numeric columns
        ontology_covariates = [
            c.column_name for c in ontology.columns if c.role == "covariate"
        ]
        extra_numeric_cols = [
            c
            for c in df.columns
            if c not in [time_col, target_col] and pd.api.types.is_numeric_dtype(df[c])
        ]

        if len(ontology_covariates) > 0 or len(extra_numeric_cols) > 0:
            covariates_present = True

        enough_data_for_ml = len(df) >= 60
        if sparsity > 0.5 or covariates_present or enough_data_for_ml:
            print("LOG: ML Specialists Triggered. Adding Skforecast variants.")
            candidates.append(SkforecastForecaster("lightgbm"))
            # candidates.append(SkforecastForecaster("rf"))  # Temporarily disabled — too slow
            candidates.append(SkforecastForecaster("xgboost"))

        # If the user has configured known_future covariates, exclude models
        # that cannot consume them — otherwise the user's planned drivers
        # would be silently ignored.
        # Naive is ALWAYS kept as a baseline for the Forecast Skill Score (FSS).
        known_future_covariates = [
            c
            for c in ontology.columns
            if c.role == "covariate"
            and getattr(c, "covariate_type", None) == "known_future"
        ]
        if known_future_covariates:
            before = len(candidates)
            # Keep Naive for FSS baseline; exclude other non-covariate models
            baseline = [m for m in candidates if isinstance(m, NaiveForecaster)]
            candidates = [m for m in candidates if m.supports_covariates]
            candidates = baseline + candidates
            print(
                f"LOG: Active known_future covariates detected ({len(known_future_covariates)}). "
                f"Filtered from {before} to {len(candidates)} models (including Naive baseline)."
            )
            if len(candidates) <= len(baseline):
                raise ValueError(
                    "No covariate-capable models available. "
                    "Please remove known_future covariate constraints or check your data."
                )

        # 3. Run Tournament
        results = []
        total_models = len(candidates)

        print(
            f"[Tournament] Starting with {total_models} models, callback: {self.progress_callback is not None}"
        )

        for idx, model in enumerate(candidates):
            model_name = model.get_metadata().name

            # Report progress at start
            if self.progress_callback:
                print(
                    f"[Tournament] Reporting progress: {idx}/{total_models} - {model_name}"
                )
                self.progress_callback(idx, total_models, model_name)

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
                        "supports_covariates": model.supports_covariates,
                    }
                )
                print(
                    f"LOG: {model.get_metadata().name} finished. MAE={mae:.4f}, MSE={mse:.4f}, Score={model.complexity_score}"
                )

                # Report progress after completion
                if self.progress_callback:
                    print(f"[Tournament] Model completed: {idx + 1}/{total_models}")
                    self.progress_callback(idx + 1, total_models, f"{model_name} ✓")

            except (ValueError, RuntimeError, TypeError) as e:
                print(f"LOG: {model.get_metadata().name} failed/crashed: {e}")

        # Report completion
        if self.progress_callback:
            self.progress_callback(total_models, total_models, "Tournament Complete")

        # 4. Selection Logic (The Rashomon Set)
        valid_results = [
            r for r in results if np.isfinite(r["mae"]) and r["mae"] >= 0.0
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

        # If known_future covariates exist, the Naive baseline must not win —
        # it would silently ignore the user's planned drivers.
        if known_future_covariates and isinstance(winner["model"], NaiveForecaster):
            covariate_winners = [
                r for r in rashomon_set if r["model"].supports_covariates
            ]
            if covariate_winners:
                winner = covariate_winners[0]
                print(
                    f"LOG: Naive was best in Rashomon set but excluded because known_future "
                    f"covariates are active. Promoted {winner['model'].get_metadata().name} to winner."
                )

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

        # Multi-Series Routing is now handled in the AutoClean layer.
        # This prevents redundant logic and ensures consistent data preparation.

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
            meta = NaiveForecaster().get_metadata()
            meta.supports_covariates = False
            return meta
        meta = self.active_model.get_metadata()
        meta.supports_covariates = self.active_model.supports_covariates
        return meta

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
                "supports_covariates": r.get(
                    "supports_covariates", model.supports_covariates
                ),
            }
            if rmse_val is not None and np.isfinite(rmse_val):
                row["rmse"] = round(rmse_val, 4)
            if mse_val is not None:
                row["mse"] = mse_val
            results.append(row)
        return results


__all__ = [
    "ARIMAForecaster",
    "ETSForecaster",
    "InternalForecaster",
    "NaiveForecaster",
    "SeasonalNaiveForecaster",
    "SmartForecastEngine",
    "SkforecastForecaster",
]
