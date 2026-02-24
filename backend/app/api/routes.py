import asyncio
import io
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.pipeline import get_pipeline
from app.domain.data import ForecastResponse
from app.domain.ontology import ForecastOntology
from app.services.progress_tracker import get_progress_tracker
from app.services.storage.database import ForecastSession, get_db

router = APIRouter()


@router.get("/forecast/progress/{session_id}")
async def stream_forecast_progress(session_id: str):
    """
    Server-Sent Events endpoint that streams forecast progress updates.
    
    Args:
        session_id: The forecast session ID to track
    
    Returns:
        SSE stream with progress updates
    """
    tracker = get_progress_tracker()
    
    async def event_generator():
        """Generate SSE events for forecast progress."""
        try:
            # Send initial state immediately
            import json
            initial_data = {
                "current": 0,
                "total": 0,
                "model_name": "Initializing...",
                "completed": False
            }
            yield f"data: {json.dumps(initial_data)}\n\n"
            
            last_state = None
            while True:
                progress = tracker.get_progress(session_id)
                
                if progress:
                    # Create state tuple to detect any changes
                    current_state = (progress.current, progress.total, progress.model_name, progress.completed)
                    
                    # Send update if state changed
                    if current_state != last_state:
                        # Format SSE message
                        data = {
                            "current": progress.current,
                            "total": progress.total,
                            "model_name": progress.model_name,
                            "completed": progress.completed
                        }
                        
                        # Send JSON data as SSE event
                        yield f"data: {json.dumps(data)}\n\n"
                        last_state = current_state
                        
                        # If completed, send final message and close
                        if progress.completed:
                            await asyncio.sleep(0.5)  # Allow client to receive final update
                            break
                
                # Poll every 100ms for more responsive updates
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            # Client disconnected
            pass
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/plan", response_model=ForecastOntology)
async def create_plan(
    file: UploadFile = File(...), prompt: str = Form(...), db: Session = Depends(get_db)
) -> ForecastOntology:
    """
    Analyzes the uploaded file and user prompt to generate a Forecast Ontology (Plan).
    Persists the initial intent and ontology.
    """
    if not file.filename or not file.filename.endswith(".csv"):
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
        # OPTIMIZATION: User requested to skip model selection at Plan stage for Frugality.
        # we only need to only choose it during our frugal tournament (in forecast).
        # pipeline.forecaster.select_model(df, ontology)
        # ontology.model_metadata = pipeline.forecaster.get_metadata()

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
        
        # Set up progress tracking callback (only if session_id exists)
        if session_id:
            tracker = get_progress_tracker()
            
            def progress_callback(current: int, total: int, model_name: str):
                """Callback that updates progress state."""
                print(f"[Progress] Callback invoked: {current}/{total} - {model_name}")
                tracker.update_progress(session_id, current, total, model_name)
            
            # Set the callback on the forecaster
            pipeline.forecaster.set_progress_callback(progress_callback)
            print(f"[Progress] Callback registered for session {session_id}")

        # FRUGAL OPTIMIZATION: Only run selection ONCE inside the pipeline.
        # pipeline.forecaster.select_model(df, ontology) -> REMOVED

        response = await asyncio.to_thread(pipeline.run_forecast, df, ontology)
        print("DEBUG: Pipeline finished.")

        # CAPTURE SELECTED MODEL METADATA
        # The pipeline has now selected a model. We must capture it to show on the final page.
        ontology.model_metadata = pipeline.forecaster.get_metadata()

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
                    db_session.cleaning_report = response.cleaning_report.model_dump()  # type: ignore[assignment]
                    db_session.forecast_results = response.forecast  # type: ignore[assignment]
                    db_session.metrics = [m.model_dump() for m in response.metrics]  # type: ignore[assignment]
                    db_session.explanation = response.explanation  # type: ignore[assignment]

                    # UPDATE ONTOLOGY with selected model
                    db_session.ontology = ontology.model_dump()  # type: ignore[assignment]

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
        raise HTTPException(status_code=400, detail=f"Invalid Ontology: {e}") from e
    except Exception as e:
        print(f"DEBUG: Unexpected error in /forecast: {e}")
        import traceback

        traceback.print_exc()
        raise e
