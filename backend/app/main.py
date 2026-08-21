from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.markets import router as markets_router, market_service
from app.api.v1.portfolio import router as portfolio_router, portfolio_service
from app.api.v1.news import router as news_router
from app.api.v1.macro import router as macro_router
from app.api.v1.technical import router as technical_router, technical_service
from app.api.v1.evidence import router as evidence_router, evidence_service
from app.api.v1.ai import router as ai_router, ai_service

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Own reusable provider connections within the active application event loop."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(12.0),
        limits=httpx.Limits(max_connections=30, max_keepalive_connections=15),
        headers={"User-Agent": "AssetPilot-AI/0.1"},
        follow_redirects=True,
    ) as provider_client:
        market_service.crypto_provider._custom_client = provider_client
        market_service.equity_provider._custom_client = provider_client
        market_service.tokenized_provider._custom_client = provider_client
        portfolio_service.account_client._custom_client = provider_client
        portfolio_service.market_service.crypto_provider._custom_client = provider_client
        technical_service.market_service.crypto_provider._custom_client = provider_client
        evidence_service.market_service.crypto_provider._custom_client = provider_client
        evidence_service.technical_service.market_service.crypto_provider._custom_client = provider_client
        ai_service.evidence_service.market_service.crypto_provider._custom_client = provider_client
        ai_service.evidence_service.technical_service.market_service.crypto_provider._custom_client = provider_client
        if hasattr(ai_service.provider, "_custom_client"):
            ai_service.provider._custom_client = provider_client
        try:
            yield
        finally:
            market_service.crypto_provider._custom_client = None
            market_service.equity_provider._custom_client = None
            market_service.tokenized_provider._custom_client = None
            portfolio_service.account_client._custom_client = None
            portfolio_service.market_service.crypto_provider._custom_client = None
            technical_service.market_service.crypto_provider._custom_client = None
            evidence_service.market_service.crypto_provider._custom_client = None
            evidence_service.technical_service.market_service.crypto_provider._custom_client = None
            ai_service.evidence_service.market_service.crypto_provider._custom_client = None
            ai_service.evidence_service.technical_service.market_service.crypto_provider._custom_client = None
            if hasattr(ai_service.provider, "_custom_client"):
                ai_service.provider._custom_client = None

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AssetPilot AI Market Intelligence & Portfolio Assistant API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configure CORS for local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(markets_router, prefix=f"{settings.API_V1_STR}/markets", tags=["Markets"])
app.include_router(portfolio_router, prefix=f"{settings.API_V1_STR}/portfolio", tags=["Portfolio"])
app.include_router(news_router, prefix=f"{settings.API_V1_STR}/news", tags=["News Intelligence"])
app.include_router(macro_router, prefix=f"{settings.API_V1_STR}/macro", tags=["Macro Intelligence"])
app.include_router(technical_router, prefix=f"{settings.API_V1_STR}/technical", tags=["Technical Intelligence"])
app.include_router(evidence_router, prefix=f"{settings.API_V1_STR}/evidence", tags=["Evidence Fusion"])
app.include_router(ai_router, prefix=f"{settings.API_V1_STR}/ai", tags=["AI Reasoning"])

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
