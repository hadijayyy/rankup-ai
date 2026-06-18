"""
RankUp AI — TikTok Shop Scraper Package
=========================================

Provides async scraping of TikTok Shop product listings and reviews
using Playwright with anti-bot detection measures.
"""

from .config import config
from .tiktok_scraper import TikTokScraper
from .review_scraper import ReviewScraper

__all__ = ["config", "TikTokScraper", "ReviewScraper"]
