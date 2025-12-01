from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import ValidationError
import pandas as pd
import io

from app.models.ontology import ForecastOntology
from app.core.intent import analyze_intent
from app.core.autoclean import clean_dataset
from app.core.forecasting import get_forecaster
from app.core.explainability import generate_explanation

router = APIRouter()

@router.post("/plan")
async def create_plan(file: UploadFile = File(...), prompt: str = Form(...)):
    """
    Analyzes the uploaded file and user prompt to generate a Forecast Ontology (Plan).
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    try:
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Analyze Intent
        ontology = analyze_intent(df, prompt)
        
        return ontology
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/forecast")
async def generate_forecast(
    file: UploadFile = File(...), 
    ontology_json: str = Form(...)
):
    """
    Executes the forecast based on the provided Ontology and Dataset.
    """
    try:
        print(f"DEBUG: Received ontology: {ontology_json}")
        # Parse Ontology
        ontology = ForecastOntology.model_validate_json(ontology_json)
        
        # Read Data
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        print(f"DEBUG: Loaded DataFrame with columns: {df.columns.tolist()}")
        
        # AutoClean
        print("DEBUG: Starting AutoClean...")
        clean_df = clean_dataset(df, ontology)
        print("DEBUG: AutoClean complete.")
        
        # Forecast
        print("DEBUG: Starting Forecast...")
        forecaster = get_forecaster(ontology)
        forecaster.fit(clean_df, ontology)
        
        horizon = ontology.requirements.horizon_requirement.steps
        forecast_df = forecaster.predict(horizon)
        print("DEBUG: Forecast complete.")
        
        # Explain
        explanation = generate_explanation(clean_df, forecast_df, ontology)
        
        return {
            "forecast": forecast_df.to_dict(orient="records"),
            "explanation": explanation,
            "metrics": {"status": "success"} # Placeholder for metrics
        }
        
    except ValidationError as e:
        print(f"ERROR: Validation Error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid Ontology: {e}")
    except Exception as e:
        print(f"ERROR: Forecast Error: {e}")
        import traceback
        with open("error.log", "w") as f:
            f.write(traceback.format_exc())
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
