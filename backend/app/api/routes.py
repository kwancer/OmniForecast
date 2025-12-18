import io
import json
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.schemas import ForecastResponse
from app.core.autoclean import clean_dataset
from app.core.database import ForecastSession, get_db
from app.core.explainability import generate_explanation
from app.core.forecasting import get_forecaster
from app.core.intent import analyze_intent
from app.models.ontology import ForecastOntology

router = APIRouter()


@router.post("/plan", response_model=ForecastOntology)
async def create_plan(
    file: UploadFile = File(...), prompt: str = Form(...), db: Session = Depends(get_db)
) -> ForecastOntology:
    """
    Analyzes the uploaded file and user prompt to generate a Forecast Ontology (Plan).
    Persists the initial intent and ontology.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        # Analyze Intent
        ontology = analyze_intent(df, prompt)

        # Generate Session ID
        session_id = str(uuid.uuid4())
        ontology.session_id = session_id

        # Determine Model and Attach Metadata
        forecaster_class = get_forecaster(ontology).__class__
        ontology.model_metadata = forecaster_class.get_metadata()

        # Persist Session
        db_session = ForecastSession(
            session_id=session_id, user_intent=prompt, ontology=ontology.model_dump()
        )
        db.add(db_session)
        db.commit()

        return ontology

    except Exception as e:
        raise e


@router.post("/forecast", response_model=ForecastResponse)
async def generate_forecast(
    file: UploadFile = File(...),
    ontology_json: str = Form(...),
    db: Session = Depends(get_db),
) -> ForecastResponse:
    """
    Executes the forecast and persists the full results and metrics.
    """
    print(f"DEBUG: /forecast called. ontology_json length: {len(ontology_json)}")
    try:
        # Parse Ontology
        print("DEBUG: Parsing ontology...")
        ontology = ForecastOntology.model_validate_json(ontology_json)

        # Ensure Metadata is available
        if not ontology.model_metadata:
            forecaster_class = get_forecaster(ontology).__class__
            ontology.model_metadata = forecaster_class.get_metadata()

        session_id = ontology.session_id
        print(f"DEBUG: Session ID: {session_id}")

        # Read Data
        print("DEBUG: Reading CSV file...")
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        print(f"DEBUG: Data shape: {df.shape}")

        # AutoClean with Audit Log
        print("DEBUG: Running AutoClean...")
        clean_df, cleaning_report = clean_dataset(df, ontology)
        print(f"DEBUG: Cleaned data shape: {clean_df.shape}")

        # Forecast with Metrics
        print("DEBUG: Getting forecaster...")
        forecaster = get_forecaster(ontology)
        print("DEBUG: Fitting model...")
        metrics = forecaster.fit(clean_df, ontology)
        print("DEBUG: Model fit successful.")

        horizon = ontology.requirements.horizon_requirement.steps
        print(f"DEBUG: Predicting horizon: {horizon}")
        forecast_df = forecaster.predict(horizon)
        print(f"DEBUG: Prediction successful. Result shape: {forecast_df.shape}")

        # Explain
        print("DEBUG: Generating explanation...")
        explanation = generate_explanation(clean_df, forecast_df, ontology, metrics)
        print("DEBUG: Explanation generated.")

        # Prepare data for JSON storage (convert Timestamps to strings)
        forecast_df_json = forecast_df.fillna(0)
        # Use pandas to_json to handle Timestamp conversion, then reload as dict
        forecast_data = json.loads(
            forecast_df_json.to_json(orient="records", date_format="iso")
        )

        metrics_data = [m.model_dump() for m in metrics]

        # Update Persisted Session
        if session_id:
            print(f"DEBUG: Updating session {session_id} in DB...")
            try:
                db_session = (
                    db.query(ForecastSession)
                    .filter(ForecastSession.session_id == session_id)
                    .first()
                )
                if db_session:
                    db_session.cleaning_report = cleaning_report.model_dump()
                    db_session.forecast_results = forecast_data
                    db_session.metrics = metrics_data
                    db_session.explanation = explanation
                    print("DEBUG: Committing to DB...")
                    db.commit()
                    print("DEBUG: DB commit successful.")
                else:
                    print(f"DEBUG: Session {session_id} not found in DB.")
            except Exception as db_err:
                print(f"DEBUG: Database error during commit: {db_err}")
                db.rollback()
                # We don't necessarily want to fail the whole request if DB fails,
                # but for this prototype it's a critical error we want to see.
                raise db_err

        print("DEBUG: Returning response.")
        return ForecastResponse(
            forecast=forecast_data,
            explanation=explanation,
            metrics=metrics,
            cleaning_report=cleaning_report,
            session_id=session_id,
        )

    except ValidationError as e:
        print(f"DEBUG: ValidationError: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Ontology: {e}")
    except Exception as e:
        print(f"DEBUG: Unexpected error in /forecast: {e}")
        import traceback

        traceback.print_exc()
        raise e
