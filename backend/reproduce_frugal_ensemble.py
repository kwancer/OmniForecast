import os
import sys

import numpy as np
import pandas as pd

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domain.ontology import (
    ColumnRoleDefinition,
    Constraints,
    ForecastOntology,
    Granularity,
    HorizonRequirement,
    MetaContext,
    ProblemDefinition,
    UserRequirements,
)
from app.layers.forecasting.engine import SmartForecastEngine


def create_ontology(target_col, time_col, sparsity=0.0):
    return ForecastOntology(
        meta=MetaContext(
            user_intent_summary="Test",
            domain_inference="Retail",
            completeness_check="complete",
        ),
        problem=ProblemDefinition(
            task_type="time_series_regression",
            granularity=Granularity(unit="day", is_regular=True),
        ),
        columns=[
            ColumnRoleDefinition(
                column_name=time_col,
                display_name="Date",
                role="time_index",
                data_type="datetime",
            ),
            ColumnRoleDefinition(
                column_name=target_col,
                display_name="Sales",
                role="target",
                data_type="continuous",
                constraints=Constraints(sparsity_ratio=sparsity),
            ),
        ],
        requirements=UserRequirements(
            primary_objective="accuracy_optimization",
            cost_function_preference="standard",
            horizon_requirement=HorizonRequirement(steps=7, flexibility="strict"),
            output_format="point_forecast",
        ),
    )


def test_scenario(name, df, ontology):
    print(f"\n--- Testing Scenario: {name} ---")
    engine = SmartForecastEngine()
    engine.fit(df, ontology)

    metadata = engine.get_metadata()
    print(f"Selected Model: {metadata.name}")
    print(f"Reason: {metadata.rationale}")

    # Simple check
    return metadata.name


def main():
    # 1. Linear Trend (Should pick SES or Holt or Damped)
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
    trend_data = np.linspace(10, 50, 100) + np.random.normal(
        0, 1, 100
    )  # Clear trend, low noise
    df_trend = pd.DataFrame({"ds": dates, "y": trend_data})

    # 2. Strong Seasonality (Should pick Holt-Winters)
    seasonal_data = (
        np.sin(np.linspace(0, 20, 100)) * 10 + 20 + np.random.normal(0, 0.5, 100)
    )
    df_seasonal = pd.DataFrame({"ds": dates, "y": seasonal_data})

    # 3. Sparse Data (Should pick Random Forest)
    sparse_data = np.zeros(100)
    sparse_data[::10] = 50  # Every 10th day has a spike
    # Add some noise to make sure it's not perfect
    df_sparse = pd.DataFrame({"ds": dates, "y": sparse_data})

    # 4. Random Walk (Should pick Naive)
    random_data = np.cumsum(np.random.normal(0, 1, 100)) + 100  # Random Walk
    df_random = pd.DataFrame({"ds": dates, "y": random_data})

    # RUN TESTS

    # Test 1: Trend
    # Sparsity low
    ont_trend = create_ontology("y", "ds", sparsity=0.0)
    # Ideally Linear Trend fits best, so Holt's Linear (Score 2) or Damped (Score 3).
    # SES (Score 1) might fail to capture trend. Naive (Score 0) will lag.
    res_trend = test_scenario("Linear Trend", df_trend, ont_trend)

    # Test 2: Seasonality
    ont_seasonal = create_ontology("y", "ds", sparsity=0.0)
    res_seasonal = test_scenario("Seasonality", df_seasonal, ont_seasonal)

    # Test 3: Sparse
    # We set sparsity > 0.5 manually in ontology to match detection logic if it was run
    # (Engine logic checks Constraints first if passed)
    # The actual data has sparsity 0.9.
    ont_sparse = create_ontology("y", "ds", sparsity=0.9)
    res_sparse = test_scenario("Sparse / Intermittent", df_sparse, ont_sparse)

    # Test 4: Random
    ont_random = create_ontology("y", "ds", sparsity=0.0)
    res_random = test_scenario("Random Walk", df_random, ont_random)


if __name__ == "__main__":
    main()
