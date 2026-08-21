import httpx
import xml.etree.ElementTree as ET
import email.utils
import logging
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.modules.news_intelligence.base import BaseNewsProvider
from app.modules.news_intelligence.schemas import (
    NewsArticle,
    NewsCategory,
    NewsDataStatus,
)
from app.modules.news_intelligence.entity_mapper import EntityMapper
from app.modules.news_intelligence.classifier import NewsClassifier
from app.modules.news_intelligence.deduplicator import NewsDeduplicator

logger = logging.getLogger(__name__)

CURATED_FEEDS = [
    {
        "name": "SEC Press Releases",
        "publisher": "U.S. Securities and Exchange Commission",
        "url": "https://www.sec.gov/news/pressreleases.rss",
        "default_category": NewsCategory.REGULATION,
    },
    {
        "name": "Federal Reserve Press",
        "publisher": "Federal Reserve System",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "default_category": NewsCategory.MONETARY_POLICY,
    },
    {
        "name": "CoinDesk",
        "publisher": "CoinDesk",
        "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "default_category": NewsCategory.CRYPTO,
    },
    {
        "name": "Yahoo Finance Market News",
        "publisher": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
        "default_category": NewsCategory.MACRO,
    }
]

class RSSNewsProvider(BaseNewsProvider):
    """News provider for curated authoritative public RSS feeds."""

    def __init__(self, feeds: Optional[List[Dict[str, Any]]] = None, timeout: float = 6.0):
        self.feeds = feeds or CURATED_FEEDS
        self.timeout = timeout
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AssetPilot/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        }

    @property
    def provider_name(self) -> str:
        return "Public RSS Feeds"

    @property
    def is_configured(self) -> bool:
        return True  # Public feeds are always available without API keys

    async def fetch_latest_news(self, limit: int = 50) -> List[NewsArticle]:
        """Fetch and parse all configured RSS feeds concurrently."""
        async with httpx.AsyncClient(timeout=self.timeout, headers=self._default_headers, follow_redirects=True) as client:
            tasks = [self._fetch_feed(feed, client) for feed in self.feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles: List[NewsArticle] = []
        for res in results:
            if isinstance(res, list):
                all_articles.extend(res)
            elif isinstance(res, Exception):
                logger.debug(f"RSS feed exception: {res}")

        # Sort by published_at descending
        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        return all_articles[:limit]

    async def fetch_company_news(self, symbol: str, limit: int = 20) -> List[NewsArticle]:
        """Filter cached RSS news for a specific symbol."""
        latest = await self.fetch_latest_news(limit=100)
        matching = [
            a for a in latest
            if any(ra.symbol.upper() == symbol.upper() for ra in a.related_assets)
        ]
        return matching[:limit]

    async def get_status(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "configured": True,
            "feeds_count": len(self.feeds),
            "feeds": [f["name"] for f in self.feeds],
            "status": "ready"
        }

    async def _fetch_feed(self, feed: Dict[str, Any], client: Optional[httpx.AsyncClient] = None) -> List[NewsArticle]:
        """Fetch and parse a single RSS feed."""
        url = feed["url"]
        articles: List[NewsArticle] = []

        try:
            owned_client = client is None
            active_client = client or httpx.AsyncClient(timeout=self.timeout, headers=self._default_headers, follow_redirects=True)
            try:
                resp = await active_client.get(url)
                if resp.status_code != 200:
                    logger.debug(f"RSS feed {feed['name']} returned HTTP {resp.status_code}")
                    return []
                
                xml_text = resp.text
                root = ET.fromstring(xml_text)
                
                channel = root.find("channel")
                items = channel.findall("item") if channel is not None else root.findall(".//item")
                if len(items) == 0:
                    items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

                for item in items[:25]:
                    article = self._parse_item(item, feed)
                    if article is not None:
                        articles.append(article)
            finally:
                if owned_client:
                    await active_client.aclose()

        except Exception as e:
            logger.debug(f"Error parsing RSS feed '{feed['name']}': {e}")

        return articles

    def _find_child(self, item: ET.Element, tags: List[str]) -> Optional[ET.Element]:
        for t in tags:
            el = item.find(t)
            if el is not None:
                return el
        return None

    def _parse_item(self, item: ET.Element, feed: Dict[str, Any]) -> Optional[NewsArticle]:
        """Extract title, link, description, pubDate from XML element."""
        try:
            title_el = self._find_child(item, ["title", "{http://www.w3.org/2005/Atom}title"])
            link_el = self._find_child(item, ["link", "{http://www.w3.org/2005/Atom}link"])
            desc_el = self._find_child(item, ["description", "{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"])
            date_el = self._find_child(item, ["pubDate", "{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"])
            guid_el = self._find_child(item, ["guid", "{http://www.w3.org/2005/Atom}id"])

            headline = (title_el.text if title_el is not None and title_el.text else "").strip()
            if not headline:
                return None

            # Clean link and enforce safe HTTP/HTTPS scheme
            url = ""
            if link_el is not None:
                url = link_el.text or link_el.get("href") or ""
                url = url.strip()

            if not url or not (url.startswith("http://") or url.startswith("https://")):
                return None

            summary_raw = desc_el.text if desc_el is not None and desc_el.text else ""
            summary = self._strip_html(summary_raw) if summary_raw else None

            external_id = (guid_el.text if guid_el is not None and guid_el.text else url).strip()

            # Date parsing
            pub_dt = datetime.now(timezone.utc)
            if date_el is not None and date_el.text:
                try:
                    pub_dt = email.utils.parsedate_to_datetime(date_el.text.strip())
                    if not pub_dt.tzinfo:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                except Exception:
                    pub_dt = datetime.now(timezone.utc)

            combined_text = f"{headline}. {summary or ''}"
            related_assets, related_companies = EntityMapper.map_entities(combined_text)

            category = NewsClassifier.classify_category(combined_text, related_assets)
            if category == NewsCategory.GENERAL and feed.get("default_category"):
                category = feed["default_category"]

            sentiment_label, sentiment_score = NewsClassifier.classify_sentiment(combined_text)
            impact_level = NewsClassifier.classify_impact(combined_text, category)
            relevance_score = NewsClassifier.calculate_relevance(
                headline=headline,
                summary=summary,
                related_assets=related_assets,
                source=feed["name"],
                published_at=pub_dt
            )

            article_id = NewsDeduplicator.generate_article_id(
                source=feed["name"],
                external_id=external_id,
                url=url
            )

            return NewsArticle(
                id=article_id,
                external_id=external_id,
                headline=headline,
                summary=summary,
                source=feed["name"],
                publisher=feed["publisher"],
                url=url,
                published_at=pub_dt,
                retrieved_at=datetime.now(timezone.utc),
                category=category,
                related_assets=related_assets,
                related_companies=related_companies,
                relevance_score=relevance_score,
                sentiment_label=sentiment_label,
                sentiment_score=sentiment_score,
                impact_level=impact_level,
                is_portfolio_relevant=False,
                portfolio_asset_match=None,
                duplicate_count=1,
                data_status=NewsDataStatus.LIVE
            )

        except Exception as e:
            logger.debug(f"Error parsing item in {feed['name']}: {e}")
            return None

    def _strip_html(self, raw_html: str) -> str:
        """Removes simple HTML tags and extra whitespace."""
        import re
        clean = re.sub(r"<[^>]+>", " ", raw_html)
        return " ".join(clean.split())
