from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.health import router as health_router
from app.api.v1.markets import router as markets_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.news import router as news_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AssetPilot AI Market Intelligence & Portfolio Assistant API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure CORS for local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(markets_router, prefix=f"{settings.API_V1_STR}/markets", tags=["Markets"])
app.include_router(portfolio_router, prefix=f"{settings.API_V1_STR}/portfolio", tags=["Portfolio"])
app.include_router(news_router, prefix=f"{settings.API_V1_STR}/news", tags=["News Intelligence"])

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
