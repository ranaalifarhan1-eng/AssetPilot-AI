from fastapi import APIRouter, HTTPException, status
import logging

from app.modules.portfolio.service import PortfolioService
from app.modules.portfolio.schemas import (
    PortfolioSummary,
    PortfolioStatusResponse,
    AccountSourcesResponse,
)

router = APIRouter()
portfolio_service = PortfolioService()

@router.get("", response_model=PortfolioSummary, summary="Get OKX Portfolio Summary")
async def get_portfolio_summary():
    """Fetch normalized read-only OKX portfolio holdings, values, and asset allocation."""
    try:
        return await portfolio_service.get_portfolio_summary()
    except Exception as e:
        logging.error(f"Unexpected error in portfolio summary endpoint: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch portfolio summary")

@router.get("/status", response_model=PortfolioStatusResponse, summary="Get Portfolio Connection Status")
async def get_portfolio_status():
    """Get metadata regarding OKX read-only portfolio integration status (never exposes API keys or secrets)."""
    try:
        return portfolio_service.get_status()
    except Exception as e:
        logging.error(f"Error fetching portfolio status: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch portfolio status")

@router.get("/accounts", response_model=AccountSourcesResponse, summary="Get Portfolio Account Sources")
async def get_account_sources():
    """Get list of supported OKX account balance areas (Trading vs Funding)."""
    try:
        status_info = portfolio_service.get_status()
        return AccountSourcesResponse(
            provider="OKX",
            sources=["Trading", "Funding"],
            configured=status_info.configured
        )
    except Exception as e:
        logging.error(f"Error fetching account sources: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch account sources")
