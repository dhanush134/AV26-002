from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def list_users(db: Session, limit: int = 100, offset: int = 0) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)))


def ensure_user(db: Session, user_id: UUID) -> User:
    user = get_user(db, user_id)
    if user is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("User not found")
    return user


def update_user(db: Session, user_id: UUID, payload: UserUpdate) -> User:
    user = ensure_user(db, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: UUID) -> None:
    user = ensure_user(db, user_id)
    db.delete(user)
    db.commit()
