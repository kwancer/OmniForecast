import asyncio
import io
import json
import uuid
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.pipeline import get_pipeline
from app.domain.data import (
    ExplainabilityRequest,
    ExplainabilityResponse,
    ForecastResponse,
)
from app.domain.ontology import ForecastOntology
from app.layers.explainability import ForecastExplainabilityService
from app.services.progress_tracker import get_progress_tracker
from app.services.storage.database import ForecastSession, SessionLocal, get_db

router = APIRouter()
explainability_service = ForecastExplainabilityService()


def _get_forecast_session(db: Session, session_id: str) -> ForecastSession:
    db_session = (
        db.query(ForecastSession)
        .filter(ForecastSession.session_id == session_id)
        .first()
    )
    if not db_session:
        raise HTTPException(status_code=404, detail="Forecast session not found")
    return db_session


def _persist_forecast_results(
    session_id: str,
    ontology: ForecastOntology,
    response: ForecastResponse,
    max_retries: int = 1,
) -> bool:
    """Persist forecast artifacts with retry for transient DB disconnects."""
    attempts = max_retries + 1

    for attempt in range(1, attempts + 1):
        db = SessionLocal()
        try:
            db_session = (
                db.query(ForecastSession)
                .filter(ForecastSession.session_id == session_id)
                .first()
            )

            if not db_session:
                print(f"DEBUG: Session {session_id} not found in DB.")
                return False

            db_session.cleaning_report = response.cleaning_report.model_dump()  # type: ignore[assignment]
            db_session.forecast_results = response.forecast  # type: ignore[assignment]
            db_session.metrics = [m.model_dump() for m in response.metrics]  # type: ignore[assignment]
            db_session.explanation = response.explanation  # type: ignore[assignment]
            ontology_payload = ontology.model_dump()
            # Persist explainability artifacts under ontology
            # to avoid DB schema migration.
            ontology_payload["_artifacts"] = {
                "data_health_report": response.data_health_report,
                "tournament_results": [
                    tr.model_dump() for tr in response.tournament_results or []
                ],
                "backtest_data": response.backtest_data,
            }
            db_session.ontology = ontology_payload  # type: ignore[assignment]

            print(f"DEBUG: Committing to DB (attempt {attempt}/{attempts})...")
            db.commit()
            print("DEBUG: DB commit successful.")
            return True

        except DBAPIError as db_err:
            db.rollback()
            is_disconnect = bool(getattr(db_err, "connection_invalidated", False))
            message = str(db_err).lower()
            if "server closed the connection unexpectedly" in message:
                is_disconnect = True

            if is_disconnect and attempt < attempts:
                print(f"DEBUG: Transient DB disconnect, retrying persistence: {db_err}")
                continue

            print(
                "DEBUG: Database error during commit "
                f"(non-retryable or exhausted): {db_err}"
            )
            return False

        except (RuntimeError, ValueError, TypeError) as db_err:
            db.rollback()
            print(f"DEBUG: Database error during commit: {db_err}")
            return False

        finally:
            db.close()

    return False


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
            initial_data = {
                "current": 0,
                "total": 0,
                "model_name": "Initializing...",
                "completed": False,
            }
            yield f"data: {json.dumps(initial_data)}\n\n"

            last_state = None
            while True:
                progress = tracker.get_progress(session_id)

                if progress:
                    # Create state tuple to detect any changes
                    current_state = (
                        progress.current,
                        progress.total,
                        progress.model_name,
                        progress.completed,
                    )

                    # Send update if state changed
                    if current_state != last_state:
                        # Format SSE message
                        data = {
                            "current": progress.current,
                            "total": progress.total,
                            "model_name": progress.model_name,
                            "completed": progress.completed,
                        }

                        # Send JSON data as SSE event
                        yield f"data: {json.dumps(data)}\n\n"
                        last_state = current_state

                        # If completed, send final message and close
                        if progress.completed:
                            await asyncio.sleep(
                                0.5
                            )  # Allow client to receive final update
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
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/forecast/explain", response_model=ExplainabilityResponse)
async def explain_forecast(
    payload: ExplainabilityRequest,
    db: Session = Depends(get_db),
) -> ExplainabilityResponse:
    """Answer a user question using grounded forecast artifacts and ontology context."""
    db_session = _get_forecast_session(db, payload.session_id)

    if not db_session.forecast_results:
        raise HTTPException(
            status_code=400, detail="Forecast is not available for this session yet"
        )

    if not payload.question.strip():
        briefing = explainability_service.generate_initial_briefing(db_session)
        # Build context for dynamic suggestions
        ctx = explainability_service._build_context(db_session)
        suggestions = explainability_service._generate_dynamic_suggestions(ctx)
        return ExplainabilityResponse(
            answer=briefing,
            evidence=[],
            suggestions=suggestions,
        )

    result = explainability_service.answer_question(
        question=payload.question,
        session=db_session,
        history=[m.model_dump() for m in (payload.history or [])],
    )
    return ExplainabilityResponse(**result)


@router.get("/forecast/explain/stream/{session_id}")
async def stream_explainability_answer(
    session_id: str,
    question: str,
    db: Session = Depends(get_db),
):
    """Streams explainability answer tokens over SSE for responsive UX."""
    db_session = _get_forecast_session(db, session_id)
    if not db_session.forecast_results:
        raise HTTPException(
            status_code=400, detail="Forecast is not available for this session yet"
        )

    async def event_generator():
        try:
            for msg_type, payload in explainability_service.synthesize_stream(
                question=question, session=db_session, history=[]
            ):
                if msg_type == "chunk":
                    yield f"data: {json.dumps({'type': 'chunk', 'text': payload})}\n\n"
                elif msg_type == "meta":
                    yield f"data: {json.dumps({'type': 'meta', **payload})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'chunk', 'text': f'error: {exc}'})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/plan", response_model=ForecastOntology)
async def create_plan(
    file: UploadFile = File(...),
    prompt: str = Form(...),
    history: Optional[str] = Form(None),
    db: Session = Depends(get_db),
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
 
        # Parse History if present
        parsed_history = None
        if history:
            try:
                parsed_history = json.loads(history)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse history JSON: {history}")
 
        # Use Pipeline
        pipeline = get_pipeline()
        ontology = pipeline.analyze_intent(df, prompt, history=parsed_history)

        # Generate Session ID
        session_id = str(uuid.uuid4())
        ontology.session_id = session_id

        # Determine Model Metadata (pipeline's forecaster can provide this)
        # OPTIMIZATION: User requested to skip model selection at Plan stage
        # for Frugality.
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
        # The pipeline has now selected a model. We must capture it to show
        # on the final page.
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

                    # UPDATE ONTOLOGY with selected model + explainability artifacts
                    ontology_payload = ontology.model_dump()
                    ontology_payload["_artifacts"] = {
                        "data_health_report": response.data_health_report,
                        "tournament_results": [
                            tr.model_dump() for tr in response.tournament_results or []
                        ],
                        "backtest_data": response.backtest_data,
                    }
                    db_session.ontology = ontology_payload  # type: ignore[assignment]

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
