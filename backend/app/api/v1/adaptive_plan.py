from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.adaptive_plan import (
    AdaptiveCheckinLogResponse,
    AdaptiveCheckinRequest,
    AdaptivePlanRequest,
    AdaptivePlanResponse,
    BiomarkerAnalysisRequest,
    BiomarkerAnalysisResponse,
    NutritionPlanResponse,
    RoutinePlanResponse,
)
from app.services import adaptive_plan_engine

router = APIRouter()


@router.post("/users/{user_id}/adaptive-plan", response_model=AdaptivePlanResponse)
def generate_adaptive_plan(user_id: UUID, payload: AdaptivePlanRequest, db: Session = Depends(get_db)):
    return adaptive_plan_engine.generate_adaptive_plan(db, user_id, payload)


@router.post("/users/{user_id}/adaptive-plan/routine", response_model=RoutinePlanResponse)
def generate_routine_plan(user_id: UUID, payload: AdaptivePlanRequest, db: Session = Depends(get_db)):
    return adaptive_plan_engine.generate_routine_plan(db, user_id, payload)


@router.post("/users/{user_id}/adaptive-plan/nutrition", response_model=NutritionPlanResponse)
def generate_nutrition_plan(user_id: UUID, payload: AdaptivePlanRequest, db: Session = Depends(get_db)):
    return adaptive_plan_engine.generate_nutrition_plan(db, user_id, payload)


@router.post("/users/{user_id}/adaptive-plan/biomarker-analysis", response_model=BiomarkerAnalysisResponse)
def analyze_biomarkers(user_id: UUID, payload: BiomarkerAnalysisRequest, db: Session = Depends(get_db)):
    return adaptive_plan_engine.analyze_biomarkers(db, user_id, payload)


@router.post("/users/{user_id}/adaptive-plan/checkin-log", response_model=AdaptiveCheckinLogResponse, status_code=201)
def save_adaptive_checkin(user_id: UUID, payload: AdaptiveCheckinRequest, db: Session = Depends(get_db)):
    adaptive_plan_engine.save_adaptive_checkin_feedback(db, user_id, payload)
    return {"user_id": user_id, "saved": True}


@router.post("/users/{user_id}/adaptive-plan/checkin", response_model=AdaptivePlanResponse, status_code=201)
def submit_adaptive_checkin(user_id: UUID, payload: AdaptiveCheckinRequest, db: Session = Depends(get_db)):
    return adaptive_plan_engine.submit_checkin_and_generate_next_plan(db, user_id, payload)
