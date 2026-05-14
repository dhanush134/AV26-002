from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.repositories import user_repository
from app.schemas.health_import_schemas import (
    AiTwinHealthContextResponse,
    DailyHealthSummaryResponse,
    DailySyncResult,
    HealthImportStorageResult,
    HealthOverviewResponse,
    HeartRateDetailResponse,
    SamsungHealthPreviewResponse,
    SamsungHealthStoredImportResponse,
    StepDetailResponse,
    StressDetailResponse,
)
from app.services.health_ai_twin_profile_service import HealthAiTwinProfileService
from app.services.health_daily_summary_service import HealthDailySummaryService
from app.services.health_daily_sync_service import run_daily_health_sync_job
from app.services.health_data_storage_service import HealthDataStorageService
from app.services.health_query_service import HealthQueryService
from app.services.samsung_health_import_service import (
    ImportOptions,
    SamsungHealthImportError,
    SamsungHealthImportService,
)


router = APIRouter(tags=["Health Data"])
samsung_service = SamsungHealthImportService()
storage_service = HealthDataStorageService()
daily_summary_service = HealthDailySummaryService()
ai_twin_profile_service = HealthAiTwinProfileService()
query_service = HealthQueryService()


async def _read_zip_upload(file: UploadFile) -> bytes:
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid Samsung Health export ZIP")
    return await file.read()


@router.post(
    "/health-imports/samsung/upload",
    response_model=SamsungHealthStoredImportResponse,
    response_model_exclude_none=True,
)
async def upload_samsung_health_export(
    file: UploadFile = File(...),
    user_id: UUID = Query(...),
    include_raw_records: bool = Query(default=False),
    include_samples: bool = Query(default=False),
    sample_limit: int = Query(default=1000, ge=0, le=50000),
    force_reprocess: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> SamsungHealthStoredImportResponse:
    user_repository.ensure_user(db, user_id)
    zip_bytes = await _read_zip_upload(file)
    try:
        storage_parse = samsung_service.parse(
            zip_bytes,
            ImportOptions(
                include_raw_records=True,
                include_samples=True,
                include_raw_extra=False,
                sample_limit=500000,
            ),
        )
        storage = storage_service.store_samsung_import(
            db,
            user_id,
            storage_parse,
            original_filename=file.filename or "samsung_health_export.zip",
            zip_bytes=zip_bytes,
            force_reprocess=force_reprocess,
        )
        if not storage.already_imported:
            from_date = min((date.fromisoformat(day) for day in storage.affected_dates), default=None)
            to_date = max((date.fromisoformat(day) for day in storage.affected_dates), default=None)
            storage.daily_summaries_updated = daily_summary_service.recompute_for_user(db, user_id, from_date, to_date)
            ai_twin_profile_service.refresh_for_user(db, user_id)
            storage.ai_twin_profile_updated = True
        db.commit()
        response_parse = samsung_service.parse(
            zip_bytes,
            ImportOptions(
                include_raw_records=include_raw_records,
                include_samples=include_samples,
                include_raw_extra=False,
                sample_limit=sample_limit,
            ),
        )
        return SamsungHealthStoredImportResponse(**response_parse.model_dump(), storage=storage)
    except SamsungHealthImportError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    except Exception:
        db.rollback()
        raise


@router.post(
    "/health-imports/samsung/preview",
    response_model=SamsungHealthPreviewResponse,
    response_model_exclude_none=True,
)
async def preview_samsung_health_export(
    file: UploadFile = File(...),
    include_debug_files: bool = Query(default=False),
) -> SamsungHealthPreviewResponse:
    zip_bytes = await _read_zip_upload(file)
    try:
        return samsung_service.preview(zip_bytes, include_debug_files=include_debug_files)
    except SamsungHealthImportError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("/health/users/{user_id}/overview", response_model=HealthOverviewResponse)
def get_health_overview(user_id: UUID, db: Session = Depends(get_db)) -> dict:
    user_repository.ensure_user(db, user_id)
    return query_service.overview(db, user_id)


@router.get("/health/users/{user_id}/daily-summaries", response_model=DailyHealthSummaryResponse)
def get_daily_summaries(
    user_id: UUID,
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
) -> dict:
    user_repository.ensure_user(db, user_id)
    return {"summaries": query_service.daily_summaries(db, user_id, from_date, to_date)}


@router.get("/health/users/{user_id}/heart-rate", response_model=HeartRateDetailResponse)
def get_heart_rate_detail(
    user_id: UUID,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
) -> dict:
    user_repository.ensure_user(db, user_id)
    return query_service.heart_rate_detail(db, user_id, from_time, to_time, limit)


@router.get("/health/users/{user_id}/steps", response_model=StepDetailResponse)
def get_step_detail(
    user_id: UUID,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
) -> dict:
    user_repository.ensure_user(db, user_id)
    return query_service.step_detail(db, user_id, from_time, to_time, limit)


@router.get("/health/users/{user_id}/stress", response_model=StressDetailResponse)
def get_stress_detail(
    user_id: UUID,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    limit: int = Query(default=1000, ge=1, le=10000),
    db: Session = Depends(get_db),
) -> dict:
    user_repository.ensure_user(db, user_id)
    return query_service.stress_detail(db, user_id, from_time, to_time, limit)


@router.get("/health/users/{user_id}/ai-twin-context", response_model=AiTwinHealthContextResponse)
def get_ai_twin_context(user_id: UUID, db: Session = Depends(get_db)) -> dict:
    user_repository.ensure_user(db, user_id)
    return query_service.ai_twin_context(db, user_id)


@router.post("/health/users/{user_id}/recompute-daily-summaries", response_model=HealthImportStorageResult)
def recompute_daily_summaries(user_id: UUID, db: Session = Depends(get_db)) -> HealthImportStorageResult:
    user_repository.ensure_user(db, user_id)
    updated = daily_summary_service.recompute_for_user(db, user_id)
    ai_twin_profile_service.refresh_for_user(db, user_id)
    db.commit()
    return HealthImportStorageResult(
        status="recomputed",
        daily_summaries_updated=updated,
        ai_twin_profile_updated=True,
    )


@router.post("/health/internal/daily-sync", response_model=DailySyncResult)
def daily_sync(
    x_internal_sync_secret: str | None = Header(default=None, alias="X-Internal-Sync-Secret"),
    db: Session = Depends(get_db),
) -> DailySyncResult:
    expected = get_settings().internal_sync_secret
    if not expected or x_internal_sync_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid internal sync secret")
    return run_daily_health_sync_job(db)
