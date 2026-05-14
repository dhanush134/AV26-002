from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.repositories import health_repository, user_repository
from app.schemas.lifestyle import LifestyleCreate, LifestyleResponse, LifestyleUpdate
from app.services.twin_engine import get_twin_snapshot

router = APIRouter()


@router.post("/users/{user_id}/lifestyle", response_model=LifestyleResponse, status_code=201)
def create_lifestyle(user_id: UUID, payload: LifestyleCreate, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    return health_repository.upsert_lifestyle(db, user_id, payload)


@router.get("/users/{user_id}/lifestyle", response_model=LifestyleResponse)
def get_lifestyle(user_id: UUID, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    profile = health_repository.get_lifestyle(db, user_id)
    if profile is None:
        raise NotFoundError("Lifestyle profile not found")
    return profile


@router.put("/users/{user_id}/lifestyle", response_model=LifestyleResponse)
def update_lifestyle(user_id: UUID, payload: LifestyleUpdate, db: Session = Depends(get_db)):
    user_repository.ensure_user(db, user_id)
    return health_repository.upsert_lifestyle(db, user_id, payload)


@router.get("/users/{user_id}/health-profile")
def get_health_profile(user_id: UUID, db: Session = Depends(get_db)):
    user = user_repository.ensure_user(db, user_id)
    return get_twin_snapshot(db, user)["current_twin"]
