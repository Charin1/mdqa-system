from fastapi import APIRouter, Depends
from ..services.analytics_service import AnalyticsService
from ..models.api import AnalyticsOverview

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
def get_overview(service: AnalyticsService = Depends(AnalyticsService)):
    return service.get_overview()

@router.get("/latency")
def get_latency(service: AnalyticsService = Depends(AnalyticsService)):
    return service.get_latency_histogram()

@router.get("/precision")
def get_precision(service: AnalyticsService = Depends(AnalyticsService)):
    return service.get_precision_at_k()