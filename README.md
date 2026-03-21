# TravelIntel AI — Central Backend

This is the main backend and admin platform for TravelIntel AI.
It provides a web dashboard for agencies to register, view analytics, and get their API keys.
It also exposes a public REST API (`/api/v1/...`) that external agency portals (like APO Agency) use to create and manage bookings.

## Architecture
- **Framework:** FastAPI (Python 3)
- **Database:** SQLite (via SQLModel)
- **Auth:** Session cookies for the web dashboard, API Keys (`X-API-Key` header) for the REST API.
- **Data Isolation:** All API endpoints automatically scope data to the agency that owns the API key.

## How to run locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `python run.py` (starts on port 8000)
3. Open `http://localhost:8000` in your browser.

## How to deploy on Render
1. Push this folder to a GitHub repository.
2. Go to [Render](https://render.com) and create a new **Web Service**.
3. Connect your GitHub repo. Render will automatically use the `render.yaml` file.
4. Add a `SECRET_KEY` environment variable in the Render dashboard.
5. Deploy!

## API Documentation
Once running, visit `/api/docs` to see the interactive Swagger UI for the public REST API.
