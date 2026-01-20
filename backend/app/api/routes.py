import io
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.pipeline import get_pipeline
from app.domain.data import ForecastResponse
from app.domain.ontology import ForecastOntology
from app.services.storage.database import ForecastSession, get_db

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

        # Use Pipeline
        pipeline = get_pipeline()
        ontology = pipeline.analyze_intent(df, prompt)

        # Generate Session ID
        session_id = str(uuid.uuid4())
        ontology.session_id = session_id

        # Determine Model Metadata (pipeline's forecaster can provide this)
        # We can access the forecaster from the pipeline instance
        # Fix: Select model first without fitting (avoiding crash on raw data)
        pipeline.forecaster.select_model(ontology)

        # Now we can safely get the metadata from the selected model
        ontology.model_metadata = pipeline.forecaster.get_metadata()

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
        session_id = ontology.session_id
        print(f"DEBUG: Session ID: {session_id}")

        # Read Data
        print("DEBUG: Reading CSV file...")
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        print(f"DEBUG: Data shape: {df.shape}")

        # Run Pipeline
        print("DEBUG: Running Pipeline...")
        pipeline = get_pipeline()

        # Ensure model is selected so we have the right model logic initialized
        pipeline.forecaster.select_model(ontology)

        # Ensure metadata is present if lost
        if not ontology.model_metadata:
            ontology.model_metadata = pipeline.forecaster.get_metadata()

        response = pipeline.run_forecast(df, ontology)
        print("DEBUG: Pipeline finished.")

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
                    db_session.cleaning_report = response.cleaning_report.model_dump()
                    db_session.forecast_results = response.forecast
                    db_session.metrics = [m.model_dump() for m in response.metrics]
                    db_session.explanation = response.explanation
                    print("DEBUG: Committing to DB...")
                    db.commit()
                    print("DEBUG: DB commit successful.")
                else:
                    print(f"DEBUG: Session {session_id} not found in DB.")
            except Exception as db_err:
                print(f"DEBUG: Database error during commit: {db_err}")
                db.rollback()
                raise db_err

        print("DEBUG: Returning response.")
        return response

    except ValidationError as e:
        print(f"DEBUG: ValidationError: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Ontology: {e}")
    except Exception as e:
        print(f"DEBUG: Unexpected error in /forecast: {e}")
        import traceback

        traceback.print_exc()
        raise e
