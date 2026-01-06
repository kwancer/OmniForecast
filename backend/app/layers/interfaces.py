from typing import List, Protocol, Tuple, Dict, Any
import pandas as pd

from app.domain.ontology import ForecastOntology
from app.domain.data import (
    CleaningReport,
    CleaningAction,
    ForecastMetric,
    ForecastResponse,
)


class IntentAnalyzer(Protocol):
    def analyze(self, df: pd.DataFrame, user_prompt: str) -> ForecastOntology:
        """
        Analyzes the dataset and user prompt to generate a Forecast Ontology.
        """
        ...


class AutoCleaner(Protocol):
    def clean(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        """
        Cleans the dataset based on the ontology.
        """
        ...


class ForecastEngine(Protocol):
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        """
        Fits the forecasting model and returns validation metrics.
        """
        ...

    def predict(self, horizon: int) -> pd.DataFrame:
        """
        Generates future predictions.
        """
        ...

    def get_metadata(self) -> Any:
        """
        Returns model metadata.
        """
        ...


class Explainer(Protocol):
    def explain(
        self,
        history_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        ontology: ForecastOntology,
        metrics: List[ForecastMetric],
    ) -> str:
        """
        Generates a natural language explanation of the forecast and metrics.
        """
        ...
