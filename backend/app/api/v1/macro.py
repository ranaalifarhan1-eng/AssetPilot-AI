import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, status

from app.modules.macro.schemas import (
    EconomicEvent,
    YieldCurveData,
    MacroStatusResponse,
)
from app.modules.macro.service import MacroService

logger = logging.getLogger(__name__)
router = APIRouter()
macro_service = MacroService()

@router.get("/status", response_model=MacroStatusResponse, summary="Get Macro Intelligence Status")
async def get_macro_status():
    """Retrieve operational status, active data sources, and event counts for the macro module."""
    try:
        return await macro_service.get_status()
    except Exception as e:
        logger.error(f"Error fetching macro status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve macro status"
        )

@router.get("/events", response_model=List[EconomicEvent], summary="Get Filtered Macro Events")
async def get_macro_events(
    category: Optional[str] = Query(None, description="Filter by category (e.g. Monetary Policy, Inflation, Labor, Growth, Liquidity / Rates)"),
    importance: Optional[str] = Query(None, description="Filter by importance: 'high', 'medium', 'low'"),
    event_status: Optional[str] = Query(None, description="Filter by status: 'upcoming', 'released', 'revised'"),
    from_date: Optional[datetime] = Query(None, description="Filter events on or after UTC datetime"),
    to_date: Optional[datetime] = Query(None, description="Filter events on or before UTC datetime"),
    limit: int = Query(50, ge=1, le=200, description="Max number of events to return")
):
    """Retrieve normalized macroeconomic events with optional category, importance, and date filtering."""
    try:
        return await macro_service.get_all_events(
            category=category,
            importance=importance,
            event_status=event_status,
            from_date=from_date,
            to_date=to_date,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error querying macro events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve macroeconomic events"
        )

@router.get("/upcoming", response_model=List[EconomicEvent], summary="Get Upcoming Macro Calendar")
async def get_upcoming_macro_events(
    window: str = Query("7d", description="Time window: 'today', '24h', '7d', '30d', 'all'"),
    limit: int = Query(20, ge=1, le=100, description="Max events to return")
):
    """Retrieve upcoming macroeconomic releases sorted soonest first."""
    try:
        return await macro_service.get_upcoming_events(window=window, limit=limit)
    except Exception as e:
        logger.error(f"Error fetching upcoming macro events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming macro events"
        )

@router.get("/recent", response_model=List[EconomicEvent], summary="Get Recent Macro Releases")
async def get_recent_macro_releases(
    limit: int = Query(20, ge=1, le=100, description="Max events to return")
):
    """Retrieve recently released macroeconomic data with actual vs forecast and surprise calculations."""
    try:
        return await macro_service.get_recent_releases(limit=limit)
    except Exception as e:
        logger.error(f"Error fetching recent macro releases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent macro releases"
        )

@router.get("/portfolio", response_model=List[EconomicEvent], summary="Get Portfolio-Relevant Macro Events")
async def get_portfolio_relevant_macro(
    limit: int = Query(20, ge=1, le=100, description="Max events to return")
):
    """Retrieve macroeconomic events that directly affect assets held in the user's connected portfolio."""
    try:
        return await macro_service.get_portfolio_relevant_events(limit=limit)
    except Exception as e:
        logger.error(f"Error fetching portfolio-relevant macro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve portfolio-relevant macro events"
        )

@router.get("/yield-curve", response_model=Optional[YieldCurveData], summary="Get U.S. Treasury Yield Curve")
async def get_treasury_yield_curve():
    """Retrieve latest official U.S. Treasury benchmark yields across 1M-30Y and 10Y-2Y spread."""
    try:
        data = await macro_service.get_yield_curve()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="U.S. Treasury Yield Curve data temporarily unavailable"
            )
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Treasury yield curve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Treasury yield curve"
        )

@router.get("/events/{event_id}", response_model=EconomicEvent, summary="Get Single Macro Event")
async def get_macro_event_by_id(event_id: str):
    """Retrieve details for a specific macroeconomic event by its unique identifier."""
    try:
        event = await macro_service.get_event_by_id(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Economic event '{event_id}' not found"
            )
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event"
        )
