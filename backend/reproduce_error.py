import requests
import json

ontology = {
  "meta": {
    "user_intent_summary": "Test",
    "domain_inference": "General",
    "completeness_check": "complete"
  },
  "problem": {
    "task_type": "time_series_regression",
    "granularity": {
      "unit": "day",
      "is_regular": True
    }
  },
  "columns": [
    {
      "column_name": "date",
      "role": "time_index",
      "data_type": "datetime",
      "future_availability": {
        "status": "known",
        "action_required": "none"
      }
    },
    {
      "column_name": "value",
      "role": "target",
      "data_type": "continuous",
      "future_availability": {
        "status": "unknown",
        "action_required": "internal_forecast"
      },
      "resampling_method": "mean" 
    }
  ],
  "requirements": {
    "primary_objective": "accuracy_optimization",
    "cost_function_preference": "standard",
    "horizon_requirement": {
      "steps": 12,
      "flexibility": "approximate"
    },
    "output_format": "point_forecast"
  }
}

# Create a dummy CSV
with open("test_data.csv", "w") as f:
    f.write("date,value\n")
    f.write("2023-01-01,10\n")
    f.write("2023-01-02,20\n")
    f.write("2023-01-03,30\n")
    f.write("2023-01-04,40\n")
    f.write("2023-01-05,50\n")

files = {'file': open('test_data.csv', 'rb')}
data = {'ontology_json': json.dumps(ontology)}

print("Sending request...")
try:
    response = requests.post('http://localhost:8001/forecast', files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
