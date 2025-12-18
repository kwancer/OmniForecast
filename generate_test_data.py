import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_data():
    # 2 years of daily data
    start_date = datetime(2022, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(730)]
    
    # Base trend + Seasonality + Noise
    t = np.linspace(0, 10, 730)
    seasonal = 10 * np.sin(2 * np.pi * t / 1.0) # Monthly-ish cycles
    trend = 2 * t
    noise = np.random.normal(0, 2, 730)
    
    values = 50 + trend + seasonal + noise
    
    df = pd.DataFrame({
        'Date': dates,
        'Daily_Sales': values.round(2),
        'Store_Region': np.random.choice(['North', 'South', 'East', 'West'], 730),
        'Promotional_Active': np.random.choice(['Yes', 'No'], 730, p=[0.2, 0.8])
    })
    
    # Introduce some gaps and NaNs to test AutoClean
    df.loc[10:15, 'Daily_Sales'] = np.nan
    df = df.drop([100, 101, 102]) # Missing timestamps
    
    df.to_csv('test_sales_data.csv', index=False)
    print("Test data 'test_sales_data.csv' generated successfully.")

if __name__ == "__main__":
    generate_test_data()
