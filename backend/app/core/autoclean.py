import pandas as pd
import numpy as np
from app.models.ontology import ForecastOntology

def clean_dataset(df: pd.DataFrame, ontology: ForecastOntology) -> pd.DataFrame:
    """
    Preprocesses the dataset based on the ontology.
    1. Identifies Time and Target columns.
    2. Converts Time to datetime.
    3. Sorts by Time.
    4. Infers frequency and reindexes (filling missing dates).
    5. Imputes missing values.
    """
    
    # Identify roles
    time_col = next((c.column_name for c in ontology.columns if c.role == "time_index"), None)
    target_col = next((c.column_name for c in ontology.columns if c.role == "target"), None)
    
    if not time_col or not target_col:
        raise ValueError("Ontology must specify a time_index and a target column.")
        
    df = df.copy()
    
    # 0. Normalize Column Names (Strip whitespace)
    df.columns = df.columns.str.strip()
    
    # Verify columns exist
    if time_col not in df.columns:
        # Try to find it case-insensitive?
        # For now just raise with better error
        raise ValueError(f"Time column '{time_col}' not found in dataset. Available: {df.columns.tolist()}")
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset. Available: {df.columns.tolist()}")

    # Ensure target is numeric BEFORE anything else
    # This prevents it from being dropped during groupby if it was object type
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
    
    # 1. Convert Time Column
    try:
        df[time_col] = pd.to_datetime(df[time_col])
    except Exception as e:
        raise ValueError(f"Could not convert {time_col} to datetime: {e}")
        
    # 2. Sort
    df = df.sort_values(time_col)
    
    # 3. Set Index
    df = df.set_index(time_col)
    
    # 4. Handle Duplicates (Aggregation)
    # Using the resampling method from ontology for the target
    target_def = next(c for c in ontology.columns if c.column_name == target_col)
    method = target_def.resampling_method
    
    if df.index.duplicated().any():
        if method == "sum":
            df = df.groupby(level=0).sum()
        elif method == "mean":
            df = df.groupby(level=0).mean()
        elif method == "last":
            df = df.groupby(level=0).last()
        elif method == "max":
            df = df.groupby(level=0).max()
        else:
            df = df.groupby(level=0).mean() # Default
            
    # 5. Infer Frequency and Reindex
    # If granularity is provided in ontology, try to use it, otherwise infer
    inferred_freq = pd.infer_freq(df.index)
    
    # Map ontology granularity to pandas freq aliases if needed
    # For now, rely on inference or default to Daily if failed
    if not inferred_freq:
        # Fallback logic based on ontology
        unit = ontology.problem.granularity.unit
        if unit == "day": inferred_freq = "D"
        elif unit == "month": inferred_freq = "MS"
        elif unit == "hour": inferred_freq = "H"
        else: inferred_freq = "D"
        
    # Reindex to fill gaps
    full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq=inferred_freq)
    df = df.reindex(full_idx)
    
    # 6. Imputation
    # Simple forward fill then backward fill for now
    # Ideally, we use interpolation for continuous variables
    if target_def.data_type == "continuous":
        df[target_col] = df[target_col].interpolate(method='linear').ffill().bfill()
    else:
        df[target_col] = df[target_col].ffill().bfill()
        
    df.index.name = time_col # Restore name
    return df.reset_index()
