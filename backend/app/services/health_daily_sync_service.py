from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.models.health_data import HealthImport
from app.schemas.health_import_schemas import DailySyncResult
from app.services.health_ai_twin_profile_service import HealthAiTwinProfileService
from app.services.health_daily_summary_service import HealthDailySummaryService


daily_summary_service = HealthDailySummaryService()
ai_twin_profile_service = HealthAiTwinProfileService()


def run_daily_health_sync_job(db: Session) -> DailySyncResult:
    today = date.today()
    start = today - timedelta(days=1)
    user_ids = list(db.scalars(select(distinct(HealthImport.user_id))))
    daily_count = 0
    profile_count = 0
    for user_id in user_ids:
        daily_count += daily_summary_service.recompute_for_user(db, user_id, start, today)
        ai_twin_profile_service.refresh_for_user(db, user_id)
        profile_count += 1
    db.commit()
    return DailySyncResult(
        status="ok",
        users_processed=len(user_ids),
        daily_summaries_updated=daily_count,
        ai_twin_profiles_updated=profile_count,
    )
