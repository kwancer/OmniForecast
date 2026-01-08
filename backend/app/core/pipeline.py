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

    def analyze_intent(self, df: pd.DataFrame, user_prompt: str) -> ForecastOntology:
        return self.intent.analyze(df, user_prompt)

    def run_forecast(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> ForecastResponse:
        # 1. AutoClean
        clean_df, cleaning_report = self.cleaner.clean(df, ontology)

        # 2. Forecast Fit
        metrics = self.forecaster.fit(clean_df, ontology)

        # 3. Forecast Predict
        horizon = ontology.requirements.horizon_requirement.steps
        forecast_df = self.forecaster.predict(horizon)

        # 4. Explain
        explanation = self.explainer.explain(clean_df, forecast_df, ontology, metrics)

        # 5. Format Output (similar to logic previously in routes)
        forecast_df_json = forecast_df.fillna(0)
        import json

        forecast_data = json.loads(
            forecast_df_json.to_json(orient="records", date_format="iso")
        )

        return ForecastResponse(
            forecast=forecast_data,
            explanation=explanation,
            metrics=metrics,
            cleaning_report=cleaning_report,
            session_id=ontology.session_id,
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
