# LifeTwin AI Backend

Production-oriented FastAPI backend for a preventive healthcare digital twin application. The API creates a current health twin from profile, lifestyle, wearable, and lab data, then generates non-diagnostic risk patterns, preventive alerts, ideal future twin goals, daily routines, day-by-day adjustments, demo streams, and doctor-facing preventive reports.

Medical safety language is intentionally non-diagnostic. Every medical-style response includes:

> This is a preventive wellness insight, not a medical diagnosis. Please consult a qualified healthcare professional for medical advice.

## Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x ORM
- Alembic
- Pydantic v2
- Uvicorn

## File Tree

```text
app/
  main.py
  core/
    config.py
    database.py
    exceptions.py
  models/
    user.py
    lifestyle.py
    wearable.py
    lab_report.py
    risk_score.py
    twin.py
    daily_checkin.py
    alert.py
  schemas/
    user.py
    lifestyle.py
    wearable.py
    lab_report.py
    risk_score.py
    twin.py
    daily_checkin.py
    alert.py
    report.py
  api/
    v1/
      router.py
      users.py
      health_profiles.py
      wearable.py
      lab_reports.py
      risk.py
      twin.py
      daily.py
      alerts.py
      reports.py
      simulation.py
  services/
    risk_engine.py
    twin_engine.py
    alert_engine.py
    daily_plan_engine.py
    simulation_engine.py
    report_service.py
  repositories/
    user_repository.py
    health_repository.py
    wearable_repository.py
    risk_repository.py
    twin_repository.py
alembic/
  env.py
  script.py.mako
  versions/
    20260514_0001_initial_schema.py
alembic.ini
requirements.txt
.env.example
README.md
```

## Setup

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database

```powershell
createdb lifetwin_ai
```

Or with `psql`:

```sql
CREATE DATABASE lifetwin_ai;
```

### 4. Configure environment

```powershell
Copy-Item .env.example .env
```

Edit `.env` if your PostgreSQL username, password, host, port, or database name differs.

### 5. Run Alembic migrations

```powershell
alembic upgrade head
```

Useful Alembic commands:

```powershell
alembic current
alembic history
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

### 6. Start the API

```powershell
uvicorn app.main:app --reload
```

### 7. Test health endpoint

```powershell
curl http://localhost:8000/health
```

Swagger docs:

```text
http://localhost:8000/docs
```

## Demo Flow

Create a realistic demo user:

```powershell
curl -X POST http://localhost:8000/api/v1/demo/create-user
```

Copy the returned `id`, then run:

```powershell
$USER_ID = "paste-user-id-here"

curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/risk/calculate"
curl "http://localhost:8000/api/v1/users/$USER_ID/twin/current"
curl "http://localhost:8000/api/v1/users/$USER_ID/twin/ideal"
curl "http://localhost:8000/api/v1/users/$USER_ID/daily-routine"
curl "http://localhost:8000/api/v1/users/$USER_ID/doctor-report"
```

Generate additional synthetic readings:

```powershell
curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/simulation/generate-readings?scenario=fatigue&days=7"
```

Run a named scenario:

```powershell
curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/simulation/run-scenario" `
  -H "Content-Type: application/json" `
  -d '{ "scenario": "cardiac_strain" }'
```

Supported simulation scenarios:

- `normal`
- `fatigue`
- `respiratory_risk`
- `cardiac_strain`
- `poor_sleep_metabolic_risk`

Submit a daily check-in and get adjustment guidance:

```powershell
curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/daily-checkin" `
  -H "Content-Type: application/json" `
  -d '{
    "sleep_quality": "poor",
    "exercise_done": "short walk",
    "food_quality": "heavy",
    "alcohol_used": true,
    "smoking_done": false,
    "stress_level": "high",
    "steps_completed": 3200,
    "sleep_hours": 5.5,
    "user_notes": "Long workday"
  }'

curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/daily-adjustment"
```

## Hackathon Demo Flow

Run migrations:

```powershell
alembic upgrade head
```

Start the server:

```powershell
uvicorn app.main:app --reload
```

Open Swagger:

```text
http://localhost:8000/docs
```

Create the full demo story:

```powershell
curl -X POST http://localhost:8000/api/v1/demo/run-full-demo
```

Set the returned user id:

```powershell
$USER_ID = "paste-user-id-here"
```

Get the frontend dashboard payload:

```powershell
curl "http://localhost:8000/api/v1/users/$USER_ID/dashboard"
```

Replay a cardiac strain scenario and return an updated dashboard:

```powershell
curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/simulation/replay" `
  -H "Content-Type: application/json" `
  -d '{ "scenario": "cardiac_strain", "points": 30 }'
```

Submit a daily check-in and receive adjusted guidance:

```powershell
curl -X POST "http://localhost:8000/api/v1/users/$USER_ID/daily-checkin" `
  -H "Content-Type: application/json" `
  -d '{
    "sleep_quality": "poor",
    "exercise_done": "short walk",
    "food_quality": "heavy",
    "alcohol_used": true,
    "smoking_done": false,
    "stress_level": "high",
    "steps_completed": 3200,
    "sleep_hours": 5.5,
    "user_notes": "Long workday"
  }'
```

Get the doctor/preventive health report:

```powershell
curl "http://localhost:8000/api/v1/users/$USER_ID/doctor-report"
```

Run the scripted demo flow:

```powershell
python scripts/demo_flow.py
```

Run smoke tests against a dedicated test database only:

```powershell
$env:TEST_DATABASE_URL="postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/lifetwin_ai_test"
pytest
```

The smoke test suite refuses to run unless `TEST_DATABASE_URL` is set and contains `test`, which helps avoid touching your normal demo database.

## Core API Groups

- Users: `/api/v1/users`
- Lifestyle: `/api/v1/users/{user_id}/lifestyle`
- Wearables: `/api/v1/users/{user_id}/wearable-readings`
- Labs: `/api/v1/users/{user_id}/lab-reports`
- Risk: `/api/v1/users/{user_id}/risk/*`
- Digital twin: `/api/v1/users/{user_id}/twin/*`
- Daily: `/api/v1/users/{user_id}/daily-*`
- Alerts: `/api/v1/users/{user_id}/alerts`
- Dashboard: `/api/v1/users/{user_id}/dashboard`
- Reports: `/api/v1/users/{user_id}/doctor-report`
- Simulation: `/api/v1/users/{user_id}/simulation/*`

## Architecture Notes

- Routers handle HTTP concerns only.
- Repositories encapsulate database access.
- Services contain deterministic scoring, twin, alert, daily plan, simulation, and report logic.
- SQLAlchemy models use UUID primary keys and timezone-aware timestamps.
- PostgreSQL JSONB stores structured risk factors, recommendations, and lifestyle history fields.
- Authentication is intentionally absent for now, but user-scoped routes and dependency-based database access make adding auth dependencies straightforward later.
