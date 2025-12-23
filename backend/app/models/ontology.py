from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class MetaContext(BaseModel):
    user_intent_summary: str
    domain_inference: str = Field(
        description="e.g., 'Financial', 'Scientific', 'Logistics', 'IoT'"
    )
    completeness_check: Literal["complete", "partial"]


class Granularity(BaseModel):
    unit: Literal["second", "minute", "hour", "day", "week", "month", "quarter", "year"]
    is_regular: bool


class ProblemDefinition(BaseModel):
    task_type: Literal[
        "time_series_regression", "time_series_classification", "anomaly_detection"
    ]
    granularity: Granularity


class FutureAvailability(BaseModel):
    status: Literal["known", "unknown", "static"]
    action_required: Literal["prompt_user", "internal_forecast", "none"]


class Constraints(BaseModel):
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_classes: Optional[List[str]] = None


class ColumnRoleDefinition(BaseModel):
    column_name: str
    role: Literal["target", "time_index", "group_id", "covariate", "ignore"]
    data_type: Literal[
        "continuous", "discrete", "binary", "categorical", "text", "datetime"
    ]
    future_availability: Optional[FutureAvailability] = None
    constraints: Optional[Constraints] = None
    resampling_method: Literal["mean", "sum", "last", "max", "none"] = "mean"


class HorizonRequirement(BaseModel):
    steps: int
    flexibility: Literal["strict", "approximate"]


class UserRequirements(BaseModel):
    primary_objective: Literal[
        "accuracy_optimization",
        "interpretability_focus",
        "probabilistic_reasoning",
        "latency_sensitive",
    ]
    cost_function_preference: Literal[
        "standard", "penalty_for_under", "penalty_for_over"
    ]
    horizon_requirement: HorizonRequirement
    output_format: Literal[
        "point_forecast", "confidence_intervals", "probability_score"
    ]


class ModelMetadata(BaseModel):
    name: str = Field(description="The friendly name of the model")
    description: str = Field(description="A brief explanation of how it works")
    rationale: str = Field(description="Why this model was chosen for this data")
    educational_video_url: Optional[str] = None


class UserIntentOntology(BaseModel):
    """
    Captured from the user's prompt and initial LLM inference.
    """
    meta: MetaContext
    problem: ProblemDefinition
    columns: List[ColumnRoleDefinition]
    requirements: UserRequirements
    session_id: Optional[str] = None


class SystemAnalysis(BaseModel):
    """
    Inferred from the data by the system (Python code).
    """
    is_daily: bool = False
    seasonality_mode: Literal["additive", "multiplicative", "none"] = "none"
    regressors: List[str] = Field(default_factory=list)


class ForecastOntology(BaseModel):
    intent: UserIntentOntology
    analysis: SystemAnalysis
    model_metadata: Optional[ModelMetadata] = None
    session_id: Optional[str] = None
