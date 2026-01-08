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


class ForecastMetric(BaseModel):
    name: str  # MAE, RMSE, MAPE
    value: float


class ForecastResponse(BaseModel):
    forecast: List[Dict[str, Any]]
    explanation: str
    metrics: List[ForecastMetric]
    cleaning_report: CleaningReport
    session_id: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    message: Optional[str] = None
    traceback: Optional[str] = None
