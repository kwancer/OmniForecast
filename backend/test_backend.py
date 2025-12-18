import json

import numpy as np
import pandas as pd
import requests

# 1. Create a dummy dataset
dates = pd.date_range(start="2023-01-01", periods=24, freq="MS")
values = np.linspace(100, 200, 24) + np.random.normal(0, 5, 24)  # Trend + Noise
df = pd.DataFrame({"Date": dates, "Sales": values})
df.to_csv("test_data.csv", index=False)

print("Created test_data.csv")

# 2. Test /plan endpoint
url_plan = "http://127.0.0.1:8000/plan"
files = {"file": open("test_data.csv", "rb")}
data = {"prompt": "Forecast sales for the next year"}

print("\nTesting /plan...")
try:
    response = requests.post(url_plan, files=files, data=data)
    if response.status_code == 200:
        ontology = response.json()
        print("Plan Success!")
        print(json.dumps(ontology, indent=2))

        # 3. Test /forecast endpoint
        url_forecast = "http://127.0.0.1:8000/forecast"
        # Re-open file as it was consumed
        files_forecast = {"file": open("test_data.csv", "rb")}
        data_forecast = {"ontology_json": json.dumps(ontology)}

        print("\nTesting /forecast...")
        response_forecast = requests.post(
            url_forecast, files=files_forecast, data=data_forecast
        )

        if response_forecast.status_code == 200:
            result = response_forecast.json()
            print("Forecast Success!")
            print("Explanation:", result["explanation"])
            print("First 3 Forecast Rows:", result["forecast"][:3])
        else:
            print("Forecast Failed:", response_forecast.text)

    else:
        print("Plan Failed:", response.text)
except Exception as e:
    print("Error:", e)
