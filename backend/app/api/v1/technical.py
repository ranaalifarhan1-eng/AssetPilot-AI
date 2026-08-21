import logging

from fastapi import APIRouter, HTTPException, Query, status

from app.modules.market_data.exceptions import InvalidAssetError, InvalidTimeframeError, ProviderUnavailableError
from app.modules.technical_analysis.schemas import MultiTimeframeResponse, TechnicalAnalysisResponse
from app.modules.technical_analysis.service import TechnicalAnalysisService

logger = logging.getLogger(__name__)
router = APIRouter()
technical_service = TechnicalAnalysisService()


@router.get("/{symbol}", response_model=TechnicalAnalysisResponse, summary="Get deterministic technical evidence")
async def get_technical_analysis(symbol: str, timeframe: str = Query("1H")):
    try:
        return await technical_service.analyze(symbol, timeframe)
    except (InvalidAssetError, InvalidTimeframeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except ProviderUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        logger.error("Technical analysis failed for %s: %s", symbol, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to compute technical analysis")


@router.get("/{symbol}/multi-timeframe", response_model=MultiTimeframeResponse, summary="Get cross-timeframe technical state")
async def get_multi_timeframe_analysis(symbol: str):
    try:
        return await technical_service.analyze_multi_timeframe(symbol)
    except InvalidAssetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Multi-timeframe analysis failed for %s: %s", symbol, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to compute multi-timeframe analysis")
