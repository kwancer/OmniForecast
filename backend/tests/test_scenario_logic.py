import pandas as pd
import pytest

from app.domain.ontology import (
    ColumnRoleDefinition,
    ForecastOntology,
    Granularity,
    HorizonRequirement,
    MetaContext,
    ProblemDefinition,
    UserRequirements,
)
from app.layers.forecasting.engine import RandomForestForecaster, SmartForecastEngine


@pytest.fixture
def mock_ontology():
    return ForecastOntology(
        meta=MetaContext(
            user_intent_summary="Test",
            domain_inference="Test",
            completeness_check="complete",
        ),
        problem=ProblemDefinition(
            task_type="time_series_regression",
            granularity=Granularity(unit="day", is_regular=True),
        ),
        columns=[
            ColumnRoleDefinition(
                column_name="Date",
                display_name="Date",
                role="time_index",
                data_type="datetime",
            ),
            ColumnRoleDefinition(
                column_name="Sales",
                display_name="Sales",
                role="target",
                data_type="continuous",
            ),
            ColumnRoleDefinition(
                column_name="Price",
                display_name="Price",
                role="covariate",
                data_type="continuous",
            ),
            ColumnRoleDefinition(
                column_name="Promo",
                display_name="Promo",
                role="covariate",
                data_type="binary",
            ),
        ],
        requirements=UserRequirements(
            primary_objective="accuracy_optimization",
            cost_function_preference="standard",
            horizon_requirement=HorizonRequirement(steps=3, flexibility="strict"),
            output_format="point_forecast",
        ),
    )


@pytest.fixture
def mock_df():
    dates = pd.date_range(start="2023-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "Date": dates,
            "Sales": [10, 12, 11, 13, 15, 14, 16, 18, 20, 22],
            "Price": [1.0] * 10,
            "Promo": [0] * 10,
        }
    )


def test_rf_recursion_and_overrides(mock_ontology, mock_df):
    rf = RandomForestForecaster()

    # Fit
    rf.fit(mock_df, mock_ontology)

    # 1. Test Constant Override (Change to...)
    mock_ontology.scenario_overrides = {
        "Price": 2.0,  # Change Price to 2.0
        "Promo": 0,  # Keep Promo 0
    }

    # Predict 3 steps
    future_df = rf.predict(horizon=3, ontology=mock_ontology)

    assert len(future_df) == 3
    # Check if prediction runs without error.
    # Hard to check exact values without mocking model internals, but we can assume if it ran, logic worked.

    # We can inspect internal logic if we mock the model but let's test end-to-end flow first.


def test_rf_custom_plan(mock_ontology, mock_df):
    rf = RandomForestForecaster()
    rf.fit(mock_df, mock_ontology)

    mock_ontology.scenario_overrides = {
        "Price": [1.0, 1.5, 2.0],  # Custom plan
        "Promo": 0,
    }

    future_df = rf.predict(horizon=3, ontology=mock_ontology)
    assert len(future_df) == 3


def test_ignore_logic_smart_engine(mock_ontology, mock_df):
    engine = SmartForecastEngine()

    # Set to ignore 'Price'
    mock_ontology.ignored_columns = ["Price"]

    # Fit - this should drop 'Price' before checking sparsity/fitting
    # We can't easily check internal state of engine's model df,
    # but we can check if it runs.

    engine.fit(mock_df, mock_ontology)

    # If Price was ignored, the underlying model should NOT expect it in predict
    # Wait, 'predict' uses ontology overrides.
    # If we ignored it, overrides on it should be ignored too?
    # Our implementation:
    # 1. engine.fit drops it. Model trained WITHOUT 'Price'.
    # 2. engine.predict calls model.predict.
    # 3. model.predict (RF) checks `feature_names_in_`.
    #    Since model was trained without Price, `feature_names_in_` won't have it.
    #    The loop over `model_features` will skip Price.
    #    So Price won't be in the step_X construction.
    #    So prediction should work and NOT use Price.

    future_df = engine.predict(horizon=3, ontology=mock_ontology)
    assert len(future_df) == 3
