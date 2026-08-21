import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.news_intelligence.schemas import (
    NewsArticle,
    NewsCategory,
    SentimentLabel,
    ImpactLevel,
    NewsDataStatus,
    RelatedAsset,
)
from app.modules.news_intelligence.entity_mapper import EntityMapper
from app.modules.news_intelligence.classifier import NewsClassifier
from app.modules.news_intelligence.deduplicator import NewsDeduplicator
from app.modules.news_intelligence.finnhub_news import FinnhubNewsProvider
from app.modules.news_intelligence.rss_news import RSSNewsProvider
from app.modules.news_intelligence.service import NewsService
from app.modules.portfolio.schemas import PortfolioSummary, PortfolioAsset
from app.modules.market_data.cache import global_cache

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_cache():
    asyncio.run(global_cache.clear())

def test_entity_mapper_crypto_mapping():
    """Verify EntityMapper extracts BTC and ETH correctly from headline/text."""
    text = "Bitcoin surges past previous resistance while Ethereum developers prepare upgrade."
    assets, companies = EntityMapper.map_entities(text)
    symbols = [a.symbol for a in assets]
    assert "BTC" in symbols
    assert "ETH" in symbols
    btc_asset = next(a for a in assets if a.symbol == "BTC")
    assert btc_asset.asset_type == "crypto"
    assert btc_asset.tokenized_symbol is None

def test_entity_mapper_equity_and_tokenized_mapping():
    """Verify EntityMapper extracts AAPL and identifies xAAPL tokenized relationship."""
    text = "Apple unveils new M4 chip lineup and announces record iPhone revenue."
    assets, companies = EntityMapper.map_entities(text)
    symbols = [a.symbol for a in assets]
    assert "AAPL" in symbols
    assert "Apple" in companies
    aapl_asset = next(a for a in assets if a.symbol == "AAPL")
    assert aapl_asset.asset_type == "equity"
    assert aapl_asset.tokenized_symbol == "xAAPL"

def test_entity_mapper_mstr_btc_cross_relationship():
    """Verify EntityMapper extracts MSTR and secondary BTC when Bitcoin purchase is reported."""
    text = "MicroStrategy acquires an additional 12,000 Bitcoin for treasury reserves."
    assets, companies = EntityMapper.map_entities(text)
    symbols = [a.symbol for a in assets]
    assert "MSTR" in symbols
    assert "BTC" in symbols
    mstr_asset = next(a for a in assets if a.symbol == "MSTR")
    assert mstr_asset.tokenized_symbol == "xMSTR"

def test_classifier_category_and_impact():
    """Verify NewsClassifier categorizes earnings and monetary policy with high impact."""
    text_earnings = "NVIDIA reports Q4 earnings beating estimates with massive data center revenue growth."
    cat_earnings = NewsClassifier.classify_category(text_earnings, [RelatedAsset(symbol="NVDA", display_symbol="NVDA", asset_type="equity", relationship_type="primary")])
    impact_earnings = NewsClassifier.classify_impact(text_earnings, cat_earnings)
    assert cat_earnings == NewsCategory.EARNINGS
    assert impact_earnings == ImpactLevel.HIGH

    text_fed = "Federal Reserve cuts interest rates by 25 basis points following FOMC meeting."
    cat_fed = NewsClassifier.classify_category(text_fed, [])
    impact_fed = NewsClassifier.classify_impact(text_fed, cat_fed)
    assert cat_fed == NewsCategory.MONETARY_POLICY
    assert impact_fed == ImpactLevel.HIGH

def test_classifier_conservative_sentiment():
    """Verify sentiment returns positive, negative, and neutral appropriately without trade signals."""
    pos_text = "Alphabet records surge in cloud profits and declares dividend increase."
    pos_label, pos_score = NewsClassifier.classify_sentiment(pos_text)
    assert pos_label == SentimentLabel.POSITIVE
    assert pos_score > 0.0

    neg_text = "SEC files lawsuit against crypto exchange alleging regulatory violations and fraud."
    neg_label, neg_score = NewsClassifier.classify_sentiment(neg_text)
    assert neg_label == SentimentLabel.NEGATIVE
    assert neg_score < 0.0

    neut_text = "Treasury releases schedule for upcoming government bond auctions."
    neut_label, neut_score = NewsClassifier.classify_sentiment(neut_text)
    assert neut_label == SentimentLabel.NEUTRAL
    assert neut_score == 0.0

def test_news_deduplicator_headline_similarity():
    """Verify deduplicator consolidates syndicated copies within time window."""
    now = datetime.now(timezone.utc)
    art1 = NewsArticle(
        id="art-1", external_id="101", headline="Fed cuts interest rates by 25 basis points amid cooling inflation",
        summary="The central bank reduced the federal funds rate today.", source="Finnhub", publisher="Reuters",
        url="https://reuters.com/article/1", published_at=now, retrieved_at=now, category=NewsCategory.MONETARY_POLICY,
        related_assets=[], related_companies=[], relevance_score=0.9, sentiment_label=SentimentLabel.NEUTRAL,
        sentiment_score=0.0, impact_level=ImpactLevel.HIGH, is_portfolio_relevant=False, portfolio_asset_match=None,
        duplicate_count=1, data_status=NewsDataStatus.LIVE
    )
    art2 = NewsArticle(
        id="art-2", external_id="102", headline="Federal Reserve cuts interest rate by 25 basis points as inflation cools",
        summary="Interest rate cut announced by the Fed.", source="Public RSS Feeds", publisher="Yahoo Finance",
        url="https://finance.yahoo.com/news/article-2", published_at=now - timedelta(minutes=15), retrieved_at=now,
        category=NewsCategory.MONETARY_POLICY, related_assets=[], related_companies=[], relevance_score=0.85,
        sentiment_label=SentimentLabel.NEUTRAL, sentiment_score=0.0, impact_level=ImpactLevel.HIGH,
        is_portfolio_relevant=False, portfolio_asset_match=None, duplicate_count=1, data_status=NewsDataStatus.LIVE
    )
    art3 = NewsArticle(
        id="art-3", external_id="103", headline="Bitcoin holds above $70,000 as institutional ETF inflows accelerate",
        summary="Crypto market experiences continuous inflows.", source="Finnhub", publisher="CoinDesk",
        url="https://coindesk.com/article-3", published_at=now - timedelta(hours=1), retrieved_at=now,
        category=NewsCategory.CRYPTO, related_assets=[RelatedAsset(symbol="BTC", display_symbol="BTC/USDT", asset_type="crypto", relationship_type="primary")],
        related_companies=[], relevance_score=0.8, sentiment_label=SentimentLabel.POSITIVE, sentiment_score=0.5,
        impact_level=ImpactLevel.MEDIUM, is_portfolio_relevant=False, portfolio_asset_match=None, duplicate_count=1,
        data_status=NewsDataStatus.LIVE
    )

    deduped = NewsDeduplicator.deduplicate([art1, art2, art3])
    assert len(deduped) == 2
    # art1 and art2 merged
    fed_article = next(a for a in deduped if "interest rate" in a.headline.lower() or "fed" in a.headline.lower())
    assert fed_article.duplicate_count == 2

@pytest.mark.asyncio
async def test_finnhub_news_provider_normalization():
    """Verify Finnhub news provider correctly parses raw JSON responses."""
    provider = FinnhubNewsProvider(api_key="mock_key")
    raw_item = {
        "category": "company",
        "datetime": 1724188800,
        "headline": "Alphabet announces new Gemini AI model capabilities for Google Cloud",
        "id": 789456,
        "image": "https://img.finnhub.io/123",
        "related": "GOOGL",
        "source": "Bloomberg",
        "summary": "Alphabet expanding cloud AI services for enterprise customers.",
        "url": "https://bloomberg.com/news/articles/2026-08-20/alphabet-gemini-cloud"
    }

    with patch.object(provider, "_fetch_json", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = [raw_item]
        articles = await provider.fetch_latest_news()

    assert len(articles) > 0
    article = articles[0]
    assert article.headline == raw_item["headline"]
    assert article.publisher == "Bloomberg"
    assert article.source == "Finnhub"
    symbols = [ra.symbol for ra in article.related_assets]
    assert "GOOGL" in symbols
    googl_asset = next(ra for ra in article.related_assets if ra.symbol == "GOOGL")
    assert googl_asset.tokenized_symbol == "xGOOGL"

def test_unsafe_url_scheme_rejected():
    """Verify provider rejects non-HTTP/HTTPS URLs to prevent javascript: or data: injection."""
    provider = FinnhubNewsProvider(api_key="mock_key")
    unsafe_item = {
        "headline": "Malicious Headline Attempt",
        "url": "javascript:alert('xss')",
        "datetime": 1724188800
    }
    result = provider._normalize_item(unsafe_item)
    assert result is None

@pytest.mark.asyncio
async def test_rss_news_provider_parsing():
    """Verify RSSNewsProvider parses sample RSS XML."""
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>SEC Press Releases</title>
        <item>
          <title>SEC Charges Major Entity with Regulatory Compliance Violations</title>
          <link>https://www.sec.gov/news/press-release/2026-99</link>
          <description>The SEC today announced charges regarding disclosure failures.</description>
          <pubDate>Thu, 20 Aug 2026 14:00:00 GMT</pubDate>
          <guid>sec-pr-2026-99</guid>
        </item>
      </channel>
    </rss>"""

    provider = RSSNewsProvider(feeds=[{
        "name": "SEC Press Releases",
        "publisher": "U.S. Securities and Exchange Commission",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "default_category": NewsCategory.REGULATION,
    }])
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = sample_xml

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        articles = await provider.fetch_latest_news()

    assert len(articles) > 0
    sec_art = articles[0]
    assert "SEC Charges" in sec_art.headline
    assert sec_art.category == NewsCategory.REGULATION
    assert sec_art.impact_level in [ImpactLevel.HIGH, ImpactLevel.MEDIUM]

@pytest.mark.asyncio
async def test_news_service_portfolio_relevance():
    """Verify NewsService marks articles matching held OKX portfolio assets."""
    now = datetime.now(timezone.utc)
    btc_article = NewsArticle(
        id="art-btc", external_id="1", headline="Bitcoin mining difficulty reaches all-time high",
        summary="Network hash rate surges.", source="Finnhub", publisher="CoinDesk", url="https://example.com/btc",
        published_at=now, retrieved_at=now, category=NewsCategory.CRYPTO,
        related_assets=[RelatedAsset(symbol="BTC", display_symbol="BTC/USDT", asset_type="crypto", relationship_type="primary")],
        related_companies=[], relevance_score=0.6, sentiment_label=SentimentLabel.POSITIVE, sentiment_score=0.4,
        impact_level=ImpactLevel.LOW, is_portfolio_relevant=False, portfolio_asset_match=None, duplicate_count=1,
        data_status=NewsDataStatus.LIVE
    )

    unrelated_article = NewsArticle(
        id="art-xyz", external_id="2", headline="Unrelated commodity market overview for wheat and corn",
        summary="Agriculture commodity updates.", source="Public RSS Feeds", publisher="Reuters", url="https://example.com/xyz",
        published_at=now, retrieved_at=now, category=NewsCategory.MACRO, related_assets=[], related_companies=[],
        relevance_score=0.4, sentiment_label=SentimentLabel.NEUTRAL, sentiment_score=0.0, impact_level=ImpactLevel.LOW,
        is_portfolio_relevant=False, portfolio_asset_match=None, duplicate_count=1, data_status=NewsDataStatus.LIVE
    )

    mock_portfolio_summary = PortfolioSummary(
        total_value_usdt="100.00",
        assets=[PortfolioAsset(symbol="BTC", name="Bitcoin", total_balance="0.5", available_balance="0.5", valuation_available=True)],
        asset_count=1, last_synced_at=now, provider="OKX", data_status="configured"
    )

    mock_provider = AsyncMock()
    mock_provider.fetch_latest_news.return_value = [btc_article, unrelated_article]
    mock_provider.is_configured = True
    mock_provider.provider_name = "MockProvider"

    mock_port_service = AsyncMock()
    mock_port_service.get_portfolio_summary.return_value = mock_portfolio_summary

    service = NewsService(providers=[mock_provider], portfolio_service=mock_port_service)
    await global_cache.set("portfolio_held_symbols", ["BTC"], ttl=60)
    res = await service.get_news(portfolio_only=True)

    assert res.total_count == 1
    assert res.articles[0].id == "art-btc"
    assert res.articles[0].is_portfolio_relevant is True
    assert res.articles[0].portfolio_asset_match == "BTC"

@pytest.mark.asyncio
async def test_news_refresh_cooldown_safety():
    """Verify refresh_news() respects 60s cooldown and does not repeat upstream calls unless forced."""
    now = datetime.now(timezone.utc)
    mock_art = NewsArticle(
        id="art-cd", external_id="1", headline="Market Overview", summary="Summary",
        source="Finnhub", publisher="Reuters", url="https://example.com/art",
        published_at=now, retrieved_at=now, category=NewsCategory.GENERAL,
        related_assets=[], related_companies=[], relevance_score=0.5,
        sentiment_label=SentimentLabel.NEUTRAL, sentiment_score=0.0, impact_level=ImpactLevel.LOW,
        is_portfolio_relevant=False, portfolio_asset_match=None, duplicate_count=1, data_status=NewsDataStatus.LIVE
    )

    mock_provider = AsyncMock()
    mock_provider.fetch_latest_news.return_value = [mock_art]
    mock_provider.is_configured = True
    mock_provider.provider_name = "MockProvider"

    service = NewsService(providers=[mock_provider])
    
    # 1. First refresh -> triggers collection
    count1, cd1 = await service.refresh_news()
    assert count1 == 1
    assert cd1 is False
    assert mock_provider.fetch_latest_news.call_count == 1

    # 2. Immediate second refresh -> cooldown active, reuses existing collection
    count2, cd2 = await service.refresh_news()
    assert count2 == 1
    assert cd2 is True
    assert mock_provider.fetch_latest_news.call_count == 1  # No extra upstream call!

    # 3. Forced refresh -> bypasses cooldown
    count3, cd3 = await service.refresh_news(force=True)
    assert count3 == 1
    assert cd3 is False
    assert mock_provider.fetch_latest_news.call_count == 2

def test_api_get_news_endpoints():
    """Verify /api/v1/news and /api/v1/news/status endpoint responses."""
    resp_status = client.get("/api/v1/news/status")
    assert resp_status.status_code == 200
    data_status = resp_status.json()
    assert "configured_sources" in data_status
    assert "provider_statuses" in data_status

    resp_news = client.get("/api/v1/news?limit=10")
    assert resp_news.status_code == 200
    data_news = resp_news.json()
    assert "articles" in data_news
    assert "total_count" in data_news
    assert "portfolio_relevant_count" in data_news
    assert isinstance(data_news["articles"], list)
