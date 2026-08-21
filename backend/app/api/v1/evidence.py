from fastapi import APIRouter, HTTPException, status

from app.modules.evidence_fusion.schemas import EvidencePackage
from app.modules.evidence_fusion.service import EvidenceFusionService
from app.modules.market_data.exceptions import InvalidAssetError

router = APIRouter()
evidence_service = EvidenceFusionService()


@router.get("/{symbol}", response_model=EvidencePackage, summary="Get provenance-rich fused evidence")
async def get_evidence(symbol: str):
    try:
        return await evidence_service.build(symbol)
    except InvalidAssetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
