from fastapi import APIRouter, HTTPException, status

from app.modules.ai_analysis.schemas import AIAnalysisResponse, AIStatusResponse
from app.modules.ai_analysis.service import AIAnalysisService
from app.modules.market_data.exceptions import InvalidAssetError

router = APIRouter()
ai_service = AIAnalysisService()


@router.get("/status", response_model=AIStatusResponse, summary="Get AI reasoning provider status")
async def get_ai_status():
    return ai_service.get_status()


@router.post("/analyze/{symbol}", response_model=AIAnalysisResponse, summary="Generate evidence-contained reasoning")
async def analyze_asset(symbol: str):
    try:
        return await ai_service.analyze(symbol)
    except InvalidAssetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
