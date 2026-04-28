import argparse
import io
import json
import os
import random
import sys
from pathlib import Path
from typing import Dict, Any, List

import httpx
import pandas as pd
import requests

def download_m3c(filepath: str):
    """Download M3C.xls if it doesn't exist."""
    url = "https://forecasters.org/data/m3comp/M3C.xls"
    print(f"Downloading M3 dataset from {url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(filepath, "wb") as f:
        f.write(response.content)
    print("Download complete.")

def parse_m3_row(row: pd.Series, sheet_name: str) -> pd.DataFrame:
    """Convert an M3 row format into a column-oriented DataFrame with a Date index."""
    # M3 format: Series, N, NF, Category, Starting Year, Starting Month/Quarter, 1, 2, 3...
    series_name = row["Series"]
    
    # Filter out empty values
    # The actual data columns start after the metadata columns
    # Find where the data starts:
    data_start_idx = 1
    while str(row.index[data_start_idx]).isalpha() or "Starting" in str(row.index[data_start_idx]) or "Unnamed" in str(row.index[data_start_idx]):
        data_start_idx += 1
        if data_start_idx >= len(row):
            break
            
    # Actually, in pandas read_excel, columns are often named 1, 2, 3...
    # Let's find numeric column names or columns that are integers
    data_cols = [col for col in row.index if isinstance(col, (int, float)) or (isinstance(col, str) and col.isdigit())]
    
    values = []
    for col in data_cols:
        val = row[col]
        if pd.notna(val) and val != "":
            values.append(val)
            
    # Ensure we only take N values as specified in the N column
    n_expected = int(row["N"]) if "N" in row else len(values)
    values = values[:n_expected]
    
    start_year = int(row["Starting Year"]) if "Starting Year" in row else 1990
    
    # Create Date index
    if sheet_name == "M3Month":
        start_month = int(row["Starting Month"]) if "Starting Month" in row else 1
        dates = pd.date_range(start=f"{start_year}-{start_month:02d}-01", periods=len(values), freq="MS")
    elif sheet_name == "M3Quarter":
        start_quarter = int(row["Starting Quarter"]) if "Starting Quarter" in row else 1
        # Convert quarter to month
        start_month = (start_quarter - 1) * 3 + 1
        dates = pd.date_range(start=f"{start_year}-{start_month:02d}-01", periods=len(values), freq="QS")
    elif sheet_name == "M3Year":
        dates = pd.date_range(start=f"{start_year}-01-01", periods=len(values), freq="YS")
    else:
        # Fallback for M3Other or unknown
        dates = pd.date_range(start=f"{start_year}-01-01", periods=len(values), freq="D")
        
    df = pd.DataFrame({
        "Date": dates,
        "Value": values
    })
    return df

def run_evaluation():
    parser = argparse.ArgumentParser(description="Evaluate OmniForecast using M3 Dataset")
    parser.add_argument("--sheet", type=str, default="M3Month", help="Sheet name in M3C.xls (e.g., M3Month, M3Year, M3Quarter, M3Other)")
    parser.add_argument("--samples", type=int, default=2, help="Number of random time series to sample")
    parser.add_argument("--save-dir", type=str, default=None, help="Directory to save generated CSVs (optional)")
    parser.add_argument("--api-url", type=str, default="http://localhost:8002", help="Base URL of the OmniForecast backend")
    parser.add_argument("--file", type=str, default="../M3C.xls", help="Path to M3C.xls file")
    
    args = parser.parse_args()
    
    # Setup paths
    m3_file = Path(args.file)
    if not m3_file.exists():
        m3_file.parent.mkdir(parents=True, exist_ok=True)
        download_m3c(str(m3_file))
        
    if args.save_dir:
        Path(args.save_dir).mkdir(parents=True, exist_ok=True)
        
    # Read the dataset
    print(f"Reading {args.sheet} from {m3_file}...")
    try:
        df_sheet = pd.read_excel(m3_file, sheet_name=args.sheet)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        print("You might need to install xlrd: pip install xlrd")
        sys.exit(1)
        
    # Sample series
    total_series = len(df_sheet)
    print(f"Found {total_series} series in {args.sheet}.")
    
    indices = list(range(total_series))
    random.shuffle(indices)
    sample_indices = indices[:args.samples]
    
    print(f"Selected {args.samples} series for evaluation.\n")
    
    results = []
    
    # Process each sampled series
    with httpx.Client(timeout=120.0) as client:
        for i, idx in enumerate(sample_indices):
            row = df_sheet.iloc[idx]
            series_name = row["Series"]
            category = row.get("Category", "Unknown")
            nf = int(row.get("NF", 12))  # Default to 12 if NF not found
            
            print(f"--- Evaluating [{i+1}/{args.samples}] Series: {series_name} (Category: {category}, NF: {nf}) ---")
            
            # 1. Parse and format the data
            df_series = parse_m3_row(row, args.sheet)
            csv_content = df_series.to_csv(index=False)
            
            # Save CSV if requested
            if args.save_dir:
                save_path = Path(args.save_dir) / f"{series_name}.csv"
                with open(save_path, "w") as f:
                    f.write(csv_content)
                print(f"Saved dataset to {save_path}")
                
            # 2. Generate Prompt
            prompt = f"Forecast the {category} time series {series_name} for the next {nf} periods."
            print(f"Prompt: \"{prompt}\"")
            
            # 3. Call POST /plan
            plan_url = f"{args.api_url}/plan"
            files = {
                "file": (f"{series_name}.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
            }
            data = {"prompt": prompt}
            
            print(f"Calling POST /plan...")
            try:
                response = client.post(plan_url, files=files, data=data)
                response.raise_for_status()
                ontology = response.json()
                print("Received Ontology successfully.")
            except Exception as e:
                print(f"Error calling /plan: {e}")
                if hasattr(e, "response") and e.response is not None:
                    print(e.response.text)
                continue
                
            # 4. Call POST /forecast
            forecast_url = f"{args.api_url}/forecast"
            
            # Prepare files again because the previous io stream was consumed
            files = {
                "file": (f"{series_name}.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")
            }
            data = {"ontology_json": json.dumps(ontology)}
            
            print(f"Calling POST /forecast...")
            try:
                response = client.post(forecast_url, files=files, data=data)
                response.raise_for_status()
                forecast_result = response.json()
                print("Received Forecast successfully.")
                
                # 5. Extract and log metrics
                metrics = forecast_result.get("metrics", [])
                print(f"Metrics for {series_name}:")
                for metric in metrics:
                    print(f"  {metric['name']}: {metric['value']:.4f}")
                    
                results.append({
                    "Series": series_name,
                    "Category": category,
                    "Metrics": metrics
                })
                
            except Exception as e:
                print(f"Error calling /forecast: {e}")
                if hasattr(e, "response") and e.response is not None:
                    print(e.response.text)
                continue
            
            print("\n")
            
    # Summary Report
    print("=== Final Summary Report ===")
    for result in results:
        metrics_str = ", ".join([f"{m['name']}={m['value']:.4f}" for m in result["Metrics"]])
        print(f"[{result['Series']}] ({result['Category']}): {metrics_str}")
        
if __name__ == "__main__":
    run_evaluation()
