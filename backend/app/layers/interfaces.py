from typing import Any, Callable, List, Optional, Protocol, Tuple

import pandas as pd

from app.domain.data import (
    CleaningReport,
    ForecastMetric,
)
from app.domain.ontology import ForecastOntology


class IntentAnalyzer(Protocol):
    def analyze(
        self,
        df: pd.DataFrame,
        user_prompt: str,
        history: Optional[list[dict[str, str]]] = None,
    ) -> ForecastOntology:
        ...


class AutoCleaner(Protocol):
    def clean(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> Tuple[pd.DataFrame, CleaningReport]:
        ...


class ForecastEngine(Protocol):
    def fit(self, df: pd.DataFrame, ontology: ForecastOntology) -> List[ForecastMetric]:
        ...

    def predict(
        self,
        horizon: int,
        ontology: Optional[ForecastOntology] = None,
        interval_width: float = 0.80,
    ) -> pd.DataFrame:
        ...

    def get_metadata(self) -> Any:
        ...

    def select_model(
        self, df: pd.DataFrame, ontology: ForecastOntology
    ) -> List[ForecastMetric]:
        ...

    def set_progress_callback(
        self, callback: Callable[[int, int, str], None] | None
    ) -> None:
        ...


class Explainer(Protocol):
    def explain(
        self,
        history_df: pd.DataFrame,
        forecast_df: pd.DataFrame,
        ontology: ForecastOntology,
        metrics: List[ForecastMetric],
    ) -> str:
        ...
