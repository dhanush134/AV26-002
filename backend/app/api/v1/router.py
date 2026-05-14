from fastapi import APIRouter

from app.api.v1 import (
    alerts,
    dashboard,
    daily,
    health_profiles,
    lab_reports,
    reports,
    risk,
    simulation,
    twin,
    users,
    wearable,
)

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(health_profiles.router, tags=["Health Profiles"])
api_router.include_router(wearable.router, tags=["Wearable"])
api_router.include_router(lab_reports.router, tags=["Lab Reports"])
api_router.include_router(risk.router, tags=["Risk"])
api_router.include_router(twin.router, tags=["Digital Twin"])
api_router.include_router(daily.router, tags=["Daily"])
api_router.include_router(alerts.router, tags=["Alerts"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(reports.router, tags=["Reports"])
api_router.include_router(simulation.router, tags=["Simulation"])
