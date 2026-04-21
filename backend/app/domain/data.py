from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class CleaningAction(BaseModel):
    column: str
    action: str  # 'imputation', 'outlier_removal', 'resampling'
    description: str


class CleaningReport(BaseModel):
    actions: List[CleaningAction] = []
    initial_shape: List[int]
    final_shape: List[int]
    summary: str
    cleaned_sample: Optional[List[Dict[str, Any]]] = None


class ForecastMetric(BaseModel):
    name: str  # MAE, RMSE, MAPE
    value: float


class TournamentResult(BaseModel):
    model_name: str
    mae: float
    complexity: float
    status: str  # 'winner', 'runner_up', 'rejected'
    metrics: List[ForecastMetric]


class ForecastResponse(BaseModel):
    forecast: List[Dict[str, Any]]
    explanation: str
    history: List[Dict[str, Any]]
    metrics: List[ForecastMetric]
    cleaning_report: CleaningReport
    session_id: Optional[str] = None
    model_metadata: Optional[Dict[str, Any]] = None
    data_health_report: Optional[Dict[str, Any]] = None
    tournament_results: Optional[List[TournamentResult]] = None
    backtest_data: Optional[List[Dict[str, Any]]] = None


class ExplainabilityMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ExplainabilityRequest(BaseModel):
    session_id: str
    question: str
    history: Optional[List[ExplainabilityMessage]] = None


class ExplainabilityEvidence(BaseModel):
    source: str
    detail: str


class ExplainabilityResponse(BaseModel):
    answer: str
    evidence: List[ExplainabilityEvidence] = []
    suggestions: List[str] = []
    tool_trace: Optional[List[Dict[str, Any]]] = None


class ErrorResponse(BaseModel):
    detail: str
    message: Optional[str] = None
    traceback: Optional[str] = None
