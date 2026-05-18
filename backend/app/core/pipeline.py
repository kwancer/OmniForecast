from typing import Optional

import pandas as pd

from app.domain.data import ForecastResponse
from app.domain.ontology import ForecastOntology
from app.layers.autoclean import RuleBasedCleaner
from app.layers.explainability import StandardExplainer
from app.layers.forecasting import SmartForecastEngine
from app.layers.intent import GeminiIntentAnalyzer
from app.layers.interfaces import AutoCleaner, Explainer, ForecastEngine, IntentAnalyzer


class ForecastPipeline:
    """
    The orchestrator that connects all layers to produce a forecast.
    """

    def __init__(
        self,
        intent: IntentAnalyzer,
        cleaner: AutoCleaner,
        forecaster: ForecastEngine,
        explainer: Explainer,
    ):
        self.intent = intent
        self.cleaner = cleaner
        self.forecaster = forecaster
        self.explainer = explainer

    def analyze_intent(
        self,
        df: pd.DataFrame,
        user_prompt: str,
        history: Optional[list[dict[str, str]]] = None,
    ) -> ForecastOntology:
        return self.intent.analyze(df, user_prompt, history=history)

    def run_forecast(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> ForecastResponse:
        clean_df, cleaning_report = self.cleaner.clean(df, ontology)

        metrics = self.forecaster.fit(clean_df, ontology)

        horizon = ontology.requirements.horizon_requirement.steps
        interval_width = getattr(ontology, "interval_width", 0.80)
        forecast_df = self.forecaster.predict(horizon, ontology, interval_width)

        explanation = self.explainer.explain(clean_df, forecast_df, ontology, metrics)

        forecast_df_json = forecast_df.fillna(0)
        import json

        history_df = clean_df.reset_index()
        history_data = json.loads(
            history_df.to_json(orient="records", date_format="iso")
        )

        forecast_data = json.loads(
            forecast_df_json.to_json(orient="records", date_format="iso")
        )

        # 6. Get the selected model's metadata
        model_metadata_obj = self.forecaster.get_metadata()

        return ForecastResponse(
            forecast=forecast_data,
            history=history_data,
            explanation=explanation,
            metrics=metrics,
            cleaning_report=cleaning_report,
            session_id=ontology.session_id,
            model_metadata=model_metadata_obj.model_dump(),
            data_health_report=self.forecaster.data_health_report,
            tournament_results=self.forecaster.get_tournament_results(),
            backtest_data=self.forecaster.get_backtest_data(),
        )


def get_pipeline() -> ForecastPipeline:
    """
    Factory to create the default pipeline.
    """
    return ForecastPipeline(
        intent=GeminiIntentAnalyzer(),
        cleaner=RuleBasedCleaner(),
        forecaster=SmartForecastEngine(),
        explainer=StandardExplainer(),
    )
