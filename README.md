Please note that Generative AI (Gemini 3.1 Pro, ChatGPT) was utilised during the development of this codebase.

As a Design Engineering project, the focus here is on system architecture, UX/UI layout, and frontend-backend integration. To accelerate development, AI tools were used to generate standard boilerplate code, configure library setups, and scaffold basic Vue/Vuetify components. All core application logic, architectural decision-making, qualitative design choices, and final integrations are the independent work of the author.

---

# AskForecast

A full-stack time-series forecasting platform. Upload a CSV, describe what you want to forecast in plain English, and receive calibrated predictions with model explanations.

## Prerequisites

- Python 3.11 or higher
- Node.js 20 or higher
- A Gemini API key from Google AI Studio

## Project Structure

```
/backend     FastAPI application (Python)
/frontend    Vue 3 + Vuetify SPA (Node.js)
```

## Environment Variables

Create a `.env` file in the `backend/` directory with the following:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Optional backend variables:

```
DATABASE_URL=sqlite:///./omniforecast.db
ALLOWED_ORIGINS=http://localhost:3000
```

Create a `.env` file in the `frontend/` directory:

```
VITE_API_URL=http://localhost:8002
VITE_ALTERNATIVE_UI=false
```

## Running the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the development server:
   ```bash
   uvicorn app.main:app --reload --port 8002
   ```

The API will be available at `http://localhost:8002`.

## Running the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The application will be available at `http://localhost:3000`.
