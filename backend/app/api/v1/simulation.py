from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.dashboard import DashboardResponse
from app.schemas.demo import FullDemoResponse
from app.schemas.user import UserResponse
from app.schemas.wearable import WearableReadingResponse
from app.services import simulation_engine

router = APIRouter()


class ScenarioRequest(BaseModel):
    scenario: str = "normal"


class ReplayRequest(BaseModel):
    scenario: str = "normal"
    points: int = Field(default=30, ge=1, le=500)


@router.post("/demo/create-user", response_model=UserResponse, status_code=201)
def create_demo_user(db: Session = Depends(get_db)):
    return simulation_engine.create_demo_user(db)


@router.post("/demo/run-full-demo", response_model=FullDemoResponse, status_code=201)
def run_full_demo(db: Session = Depends(get_db)):
    return simulation_engine.run_full_demo(db)


@router.post("/users/{user_id}/simulation/generate-readings", response_model=list[WearableReadingResponse], status_code=201)
def generate_simulated_readings(
    user_id: UUID,
    scenario: str = Query(default="normal"),
    days: int = Query(default=7, ge=1, le=60),
    db: Session = Depends(get_db),
):
    return simulation_engine.generate_readings(db, user_id, scenario=scenario, days=days)


@router.post("/users/{user_id}/simulation/run-scenario")
def run_scenario(user_id: UUID, payload: ScenarioRequest, db: Session = Depends(get_db)):
    return simulation_engine.run_scenario(db, user_id, payload.scenario)


@router.post("/users/{user_id}/simulation/replay", response_model=DashboardResponse)
def replay_scenario(user_id: UUID, payload: ReplayRequest, db: Session = Depends(get_db)):
    return simulation_engine.replay_scenario(db, user_id, payload.scenario, payload.points)
