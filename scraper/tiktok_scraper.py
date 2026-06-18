"""
RankUp AI — TikTok Shop Product Scraper
=========================================

Async Playwright-based scraper for TikTok Shop product listings.
Includes anti-bot detection measures: random delays, user agent rotation,
headless mode, and viewport randomization.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

from playwright.async_api import async_playwright, Browser, Page, Response

from .config import config

logger = logging.getLogger(__name__)


class TikTokScraper:
    """
    Scrapes TikTok Shop product listing pages using Playwright.

    Usage::

        scraper = TikTokScraper()
        product = await scraper.scrape_product("https://www.tiktok.com/@shop/product/...")
        products = await scraper.scrape_shop_products("https://www.tiktok.com/@shop/...")
        await scraper.close()
    """

    def __init__(self) -> None:
        self._browser: Optional[Browser] = None
        self._playwright = None

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    async def _ensure_browser(self) -> Browser:
        """Lazily launch the Playwright browser (one instance per scraper)."""
        if self._browser is not None and self._browser.is_connected():
            return self._browser

        self._playwright = await async_playwright().start()

        launch_options: Dict[str, Any] = {
            "headless": config.scraper.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size={},{}".format(
                    config.scraper.viewport_width, config.scraper.viewport_height
                ),
            ],
        }

        # Proxy support
        proxy_url = config.proxy.proxy_url
        if proxy_url:
            launch_options["proxy"] = {"server": proxy_url}

        self._browser = await self._playwright.chromium.launch(**launch_options)
        logger.info("Playwright browser launched (headless=%s)", config.scraper.headless)
        return self._browser

    async def _new_page(self) -> Page:
        """Create a new browser page with anti-detection tweaks."""
        browser = await self._ensure_browser()
        context = await browser.new_context(
            viewport={
                "width": config.scraper.viewport_width,
                "height": config.scraper.viewport_height,
            },
            user_agent=random.choice(config.user_agents),
            locale="en-US",
            timezone_id="America/New_York",
            # Block cookies/modals banners
            permissions=[],
            java_script_enabled=True,
            ignore_https_errors=False,
        )
        page = await context.new_page()

        # Remove webdriver痕迹
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """
        )

        return page

    async def _random_delay(self, min_s: float | None = None, max_s: float | None = None) -> None:
        """Sleep a random amount of time to simulate human behaviour."""
        delay = random.uniform(
            min_s or config.scraper.min_delay,
            max_s or config.scraper.max_delay,
        )
        logger.debug("Delaying %.2f s", delay)
        await asyncio.sleep(delay)

    async def close(self) -> None:
        """Release browser resources."""
        if self._browser and self._browser.is_connected():
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None
        logger.info("Playwright browser closed")

    # ------------------------------------------------------------------
    # Scraping logic
    # ------------------------------------------------------------------

    async def scrape_product(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single TikTok Shop product page.

        Args:
            url: Full URL of the TikTok Shop product page.

        Returns:
            dict with keys:
                title, description, price, images (list of URLs),
                hashtags (list), sales_count (int), rating (float),
                review_count (int), url (str).

        Raises:
            ValueError: If the URL is empty or invalid.
            RuntimeError: If scraping fails after retries.
        """
        if not url:
            raise ValueError("Product URL must not be empty")

        last_exception: Optional[Exception] = None
        for attempt in range(1, config.scraper.retry_count + 1):
            try:
                return await self._scrape_product_single(url)
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    "Attempt %d/%d failed for %s: %s",
                    attempt,
                    config.scraper.retry_count,
                    url,
                    exc,
                )
                if attempt < config.scraper.retry_count:
                    await asyncio.sleep(config.scraper.retry_delay * attempt)

        raise RuntimeError(
            f"Failed to scrape product after {config.scraper.retry_count} attempts: {url}"
        ) from last_exception

    async def _scrape_product_single(self, url: str) -> Dict[str, Any]:
        """Inner scrape logic for a single product page."""
        page = await self._new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=config.scraper.navigation_timeout)
            await self._random_delay()

            # Wait for the product content to load
            await page.wait_for_load_state("domcontentloaded", timeout=config.scraper.page_load_timeout)

            # Give dynamic content time to render
            await self._random_delay(2.0, 4.0)

            # --- Extract data via page evaluation ---
            product_data: Dict[str, Any] = await page.evaluate(
                """
                () => {
                    const data = {};

                    // Title – try common selectors
                    const titleEl = document.querySelector('h1')
                        || document.querySelector('[data-e2e="product-title"]')
                        || document.querySelector('.product-title')
                        || document.querySelector('meta[property="og:title"]');
                    data.title = titleEl
                        ? (titleEl.textContent || titleEl.content || '').trim()
                        : '';

                    // Description
                    const descEl = document.querySelector('[data-e2e="product-desc"]')
                        || document.querySelector('.product-description')
                        || document.querySelector('meta[property="og:description"]')
                        || document.querySelector('meta[name="description"]');
                    data.description = descEl
                        ? (descEl.textContent || descEl.content || '').trim()
                        : '';

                    // Price
                    const priceEl = document.querySelector('[data-e2e="product-price"]')
                        || document.querySelector('.product-price')
                        || document.querySelector('.price');
                    data.price = priceEl ? priceEl.textContent.trim() : '';
                    if (!data.price) {
                        const priceMeta = document.querySelector('meta[property="product:price:amount"]');
                        data.price = priceMeta ? priceMeta.content : '';
                    }

                    // Images
                    const imgEls = document.querySelectorAll('img[data-e2e="product-image"], .product-gallery img, .product-image img, img[src*="tiktok"][src*="image"]');
                    data.images = Array.from(imgEls).slice(0, 10).map(img => img.src || img.getAttribute('data-src')).filter(Boolean);

                    // Sales count
                    const salesEl = document.querySelector('[data-e2e="product-sales"]')
                        || document.querySelector('.product-sales')
                        || document.querySelector('[class*="sales"]');
                    data.sales_count = 0;
                    if (salesEl) {
                        const text = salesEl.textContent.trim();
                        const match = text.match(/(\\d[\d,]*)/);
                        if (match) data.sales_count = parseInt(match[1].replace(/,/g, ''), 10) || 0;
                    }

                    // Rating
                    const ratingEl = document.querySelector('[data-e2e="product-rating"]')
                        || document.querySelector('.product-rating')
                        || document.querySelector('[class*="rating"]');
                    data.rating = 0.0;
                    if (ratingEl) {
                        const text = ratingEl.textContent.trim();
                        const match = text.match(/(\\d+\\.?\\d*)/);
                        if (match) data.rating = parseFloat(match[1]) || 0.0;
                    }

                    // Review count
                    const reviewEl = document.querySelector('[data-e2e="review-count"]')
                        || document.querySelector('.review-count')
                        || document.querySelector('[class*="review"]');
                    data.review_count = 0;
                    if (reviewEl) {
                        const text = reviewEl.textContent.trim();
                        const match = text.match(/(\\d[\d,]*)/);
                        if (match) data.review_count = parseInt(match[1].replace(/,/g, ''), 10) || 0;
                    }

                    // Hashtags – from product description or hashtag elements
                    const hashtagEls = document.querySelectorAll('[data-e2e="product-hashtag"], .product-hashtag, a[href*="tag"]');
                    data.hashtags = Array.from(hashtagEls).map(el => el.textContent.trim()).filter(t => t.startsWith('#') || t);

                    // Also extract hashtags from description
                    if (data.description) {
                        const descTags = data.description.match(/#[\\w]+/g);
                        if (descTags) {
                            data.hashtags = [...new Set([...data.hashtags, ...descTags])];
                        }
                    }

                    return data;
                }
                """
            )

            # Normalise / fill fallbacks
            product_data.setdefault("title", "")
            product_data.setdefault("description", "")
            product_data.setdefault("price", "")
            product_data.setdefault("images", [])
            product_data.setdefault("hashtags", [])
            product_data.setdefault("sales_count", 0)
            product_data.setdefault("rating", 0.0)
            product_data.setdefault("review_count", 0)
            product_data["url"] = url

            logger.info(
                "Scraped product: '%s' | price=%s | rating=%.1f | sales=%d",
                product_data["title"][:60],
                product_data["price"],
                product_data["rating"],
                product_data["sales_count"],
            )

            return product_data

        finally:
            await page.close()

    async def scrape_shop_products(self, shop_url: str, max_products: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape all product listings from a TikTok Shop page.

        Args:
            shop_url: URL of the TikTok Shop storefront.
            max_products: Maximum number of products to scrape (default 50).

        Returns:
            List of product dicts (same structure as :meth:`scrape_product`).

        Raises:
            ValueError: If shop_url is empty.
            RuntimeError: If scraping fails after retries.
        """
        if not shop_url:
            raise ValueError("Shop URL must not be empty")

        results: List[Dict[str, Any]] = []
        seen_urls: set = set()

        page = await self._new_page()
        try:
            await page.goto(shop_url, wait_until="networkidle", timeout=config.scraper.navigation_timeout)
            await self._random_delay()

            # Scroll to load lazy products
            for scroll_step in range(5):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await self._random_delay(1.0, 2.5)

            # Collect product links
            product_links: List[str] = await page.evaluate(
                """
                () => {
                    const links = new Set();
                    document.querySelectorAll('a[href*="/product/"], a[href*="/item/"], [data-e2e="product-card"] a, .product-card a, a[href*="/shop/"]')
                        .forEach(el => {
                            const href = el.href || el.getAttribute('href') || '';
                            if (href && (href.includes('/product/') || href.includes('/item/'))) {
                                links.add(href.startsWith('http') ? href : 'https://www.tiktok.com' + href);
                            }
                        });
                    return Array.from(links);
                }
                """
            )

            logger.info("Found %d product links on shop page", len(product_links))

            for link in product_links[:max_products]:
                if link in seen_urls:
                    continue
                seen_urls.add(link)
                try:
                    product = await self.scrape_product(link)
                    results.append(product)
                except Exception as exc:
                    logger.error("Failed to scrape product %s: %s", link, exc)
                    continue

            return results

        finally:
            await page.close()

    async def __aenter__(self) -> "TikTokScraper":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
