from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class CovariateType(str, Enum):
    """Classification of covariate types for frugal forecasting."""

    CONTROLLABLE = "controllable"  # e.g., Price, Promotion, Staffing (User Decides)
    EXOGENOUS = "exogenous"  # e.g., Weather, Competitor Price (External)
    STATIC = "static"  # e.g., Store Location (Ignored for time-series)


class MetaContext(BaseModel):
    user_intent_summary: str
    domain_inference: str = Field(
        description="e.g., 'Financial', 'Scientific', 'Logistics', 'IoT'"
    )
    completeness_check: Literal["complete", "partial"]
    confidence_score: float = Field(
        default=1.0,
        description="LLM's confidence in the generated ontology (0.0 to 1.0).",
    )
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="Questions to ask the user if confidence is low.",
    )


class Granularity(BaseModel):
    unit: Literal["second", "minute", "hour", "day", "week", "month", "quarter", "year"]
    is_regular: bool


class ProblemDefinition(BaseModel):
    task_type: Literal[
        "time_series_regression", "time_series_classification", "anomaly_detection"
    ]
    granularity: Granularity
    confidence_score: float = 1.0
    confidence_rationale: Optional[str] = None


class FutureAvailability(BaseModel):
    status: Literal["known", "unknown", "static"]
    action_required: Literal["prompt_user", "internal_forecast", "none"]


class Constraints(BaseModel):
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_classes: Optional[List[str]] = None
    sparsity_ratio: Optional[float] = Field(
        default=None,
        description="The ratio of zeros to total observations (0.0 - 1.0).",
    )


class ColumnRoleDefinition(BaseModel):
    column_name: str
    display_name: str
    role: Literal["target", "time_index", "group_id", "covariate", "ignore"]
    data_type: Literal[
        "continuous", "discrete", "binary", "categorical", "text", "datetime"
    ]
    covariate_type: Optional[CovariateType] = None
    future_availability: Optional[FutureAvailability] = None
    constraints: Optional[Constraints] = None
    resampling_method: Literal["mean", "sum", "last", "max", "none"] = "mean"
    date_format: Optional[str] = Field(
        default=None,
        description=(
            "Python strftime format string for parsing date/time columns. "
            "Examples: '%Y-%m-%d' for '2024-01-15', '%y-%m-%d' for '24-01-15', "
            "'%d/%m/%Y' for '15/01/2024'. Only needed for time_index columns."
        ),
    )
    confidence_score: float = 1.0
    confidence_rationale: Optional[str] = None


class HorizonRequirement(BaseModel):
    steps: int
    flexibility: Literal["strict", "approximate"]
    confidence_score: float = 1.0
    confidence_rationale: Optional[str] = None


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


class ForecastOntology(BaseModel):
    meta: MetaContext
    problem: ProblemDefinition
    columns: List[ColumnRoleDefinition]
    requirements: UserRequirements
    model_metadata: Optional[ModelMetadata] = None
    session_id: Optional[str] = None
    sample_data: Optional[List[Dict[str, Any]]] = None
    scenario_overrides: Optional[Dict[str, Union[float, List[float], None]]] = None
    ignored_columns: Optional[List[str]] = None
    # Risk Preference & Confidence Intervals
    risk_preference: Literal["balanced", "under_penalty", "over_penalty"] = "balanced"
    interval_width: float = Field(
        default=0.80,
        description=(
            "Width of the prediction interval (0.80 = P10/P90, 0.95 = P2.5/P97.5)"
        ),
    )
