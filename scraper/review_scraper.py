"""
RankUp AI — TikTok Shop Review Scraper
========================================

Async Playwright-based scraper for TikTok Shop product reviews.
Extracts review text, ratings, reviewer info, and metadata.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from .config import config
from .tiktok_scraper import TikTokScraper

logger = logging.getLogger(__name__)


class ReviewScraper:
    """
    Scrapes reviews from TikTok Shop product pages.

    Usage::

        scraper = ReviewScraper()
        reviews = await scraper.scrape_reviews("https://www.tiktok.com/@shop/product/...", max_reviews=50)
        all_reviews = await scraper.scrape_all_reviews("https://www.tiktok.com/@shop/...")
        await scraper.close()
    """

    def __init__(self, tiktok_scraper: Optional[TikTokScraper] = None) -> None:
        self._scraper = tiktok_scraper or TikTokScraper()

    async def _random_delay(self, min_s: float | None = None, max_s: float | None = None) -> None:
        delay = random.uniform(
            min_s or config.scraper.min_delay,
            max_s or config.scraper.max_delay,
        )
        await asyncio.sleep(delay)

    async def _scroll_review_feed(self, page: Page, target_count: int) -> None:
        """
        Scroll the review list to trigger lazy-loading of more reviews.
        Continues until target_count is reached or no new content loads.
        """
        last_height = 0
        stalled_scrolls = 0
        max_stalled = 5

        for _ in range(30):  # safety cap
            # Count current review items
            current_count = await page.evaluate(
                """
                () => {
                    return document.querySelectorAll(
                        '[data-e2e="review-item"], .review-item, [class*="review-card"], [class*="ReviewItem"]'
                    ).length;
                }
                """
            )

            if current_count >= target_count:
                logger.info("Reached target review count: %d", current_count)
                break

            # Scroll down inside the review container
            await page.evaluate(
                """
                () => {
                    const container = document.querySelector('.review-list, .review-section, [class*="reviewList"]');
                    if (container) {
                        container.scrollTop = container.scrollHeight;
                    } else {
                        window.scrollBy(0, 600);
                    }
                }
                """
            )
            await self._random_delay(1.0, 2.5)

            # Check height progress
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                stalled_scrolls += 1
                if stalled_scrolls >= max_stalled:
                    logger.info("Review feed stalled after %d scrolls", stalled_scrolls)
                    break
            else:
                stalled_scrolls = 0
            last_height = new_height

    async def scrape_reviews(
        self,
        product_url: str,
        max_reviews: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Scrape reviews for a single product.

        Args:
            product_url: TikTok Shop product page URL.
            max_reviews: Maximum number of reviews to collect (default 100).

        Returns:
            List of dicts with keys:
                reviewer_name, rating (float), text, date, helpful_count (int).

        Raises:
            ValueError: If product_url is empty.
            RuntimeError: If scraping fails after retries.
        """
        if not product_url:
            raise ValueError("Product URL must not be empty")

        last_exception: Optional[Exception] = None
        for attempt in range(1, config.scraper.retry_count + 1):
            try:
                return await self._scrape_reviews_single(product_url, max_reviews)
            except Exception as exc:
                last_exception = exc
                logger.warning(
                    "Review scrape attempt %d/%d failed for %s: %s",
                    attempt, config.scraper.retry_count, product_url, exc,
                )
                if attempt < config.scraper.retry_count:
                    await asyncio.sleep(config.scraper.retry_delay * attempt)

        raise RuntimeError(
            f"Failed to scrape reviews after {config.scraper.retry_count} attempts: {product_url}"
        ) from last_exception

    async def _scrape_reviews_single(
        self,
        product_url: str,
        max_reviews: int,
    ) -> List[Dict[str, Any]]:
        page = await self._scraper._new_page()
        try:
            await page.goto(
                product_url,
                wait_until="networkidle",
                timeout=config.scraper.navigation_timeout,
            )
            await self._random_delay(2.0, 4.0)

            # Try to click the "Reviews" tab / expand reviews section
            try:
                review_tab_selectors = [
                    '[data-e2e="reviews-tab"]',
                    '[data-e2e="review-tab"]',
                    'button:has-text("Reviews")',
                    '[class*="reviewTab"]',
                    'a:has-text("Reviews")',
                    '[class*="review-section"]',
                ]
                for sel in review_tab_selectors:
                    tab = await page.query_selector(sel)
                    if tab:
                        await tab.click()
                        await self._random_delay(1.0, 2.0)
                        logger.info("Clicked review tab: %s", sel)
                        break
            except Exception:
                logger.debug("No review tab found; assuming reviews are already visible")

            # Scroll to load reviews
            await self._scroll_review_feed(page, max_reviews)

            # Extract reviews from the DOM
            reviews: List[Dict[str, Any]] = await page.evaluate(
                """
                (maxReviews) => {
                    const items = document.querySelectorAll(
                        '[data-e2e="review-item"], .review-item, [class*="review-card"], [class*="ReviewItem"]'
                    );
                    const results = [];
                    for (const item of items) {
                        if (results.length >= maxReviews) break;

                        // Reviewer name
                        const nameEl = item.querySelector('[data-e2e="reviewer-name"], .reviewer-name, [class*="username"], [class*="reviewer"]');
                        const reviewer_name = nameEl ? nameEl.textContent.trim() : '';

                        // Rating
                        const ratingEl = item.querySelector('[data-e2e="review-rating"], .review-rating, [class*="rating"], [class*="star"]');
                        let rating = 0.0;
                        if (ratingEl) {
                            const text = ratingEl.textContent.trim();
                            const match = text.match(/(\\d+\\.?\\d*)/);
                            if (match) rating = parseFloat(match[1]) || 0.0;
                        }

                        // Star-filled elements (alt approach: count filled stars)
                        if (!rating) {
                            const filledStars = item.querySelectorAll('.star-filled, [class*="star"][class*="fill"], [data-filled="true"]').length;
                            if (filledStars > 0) rating = filledStars;
                        }

                        // Review text
                        const textEl = item.querySelector('[data-e2e="review-text"], .review-text, [class*="reviewContent"], [class*="comment-text"], p');
                        const text = textEl ? textEl.textContent.trim() : '';

                        // Date
                        const dateEl = item.querySelector('[data-e2e="review-date"], .review-date, [class*="date"], [class*="time"], time');
                        const date = dateEl ? (dateEl.textContent || dateEl.getAttribute('datetime') || '').trim() : '';

                        // Helpful count
                        const helpfulEl = item.querySelector('[data-e2e="helpful-count"], .helpful-count, [class*="helpful"], [class*="like-count"], [class*="vote"]');
                        let helpful_count = 0;
                        if (helpfulEl) {
                            const text = helpfulEl.textContent.trim();
                            const match = text.match(/(\\d[\d,]*)/);
                            if (match) helpful_count = parseInt(match[1].replace(/,/g, ''), 10) || 0;
                        }

                        if (reviewer_name || text) {
                            results.push({ reviewer_name, rating, text, date, helpful_count });
                        }
                    }
                    return results;
                }
                """,
                max_reviews,
            )

            logger.info("Extracted %d reviews from %s", len(reviews), product_url)
            return reviews

        finally:
            await page.close()

    async def scrape_all_reviews(self, shop_url: str) -> Dict[str, Any]:
        """
        Scrape all reviews for all products in a TikTok Shop.

        Args:
            shop_url: TikTok Shop storefront URL.

        Returns:
            dict with keys:
                shop_url, total_products (int), total_reviews (int),
                products (list of dicts: {product_url, title, reviews})
        """
        if not shop_url:
            raise ValueError("Shop URL must not be empty")

        logger.info("Scraping all products and reviews from shop: %s", shop_url)
        products = await self._scraper.scrape_shop_products(shop_url)
        logger.info("Found %d products in shop", len(products))

        result_products = []
        total_reviews = 0

        for product in products:
            product_url = product.get("url", "")
            if not product_url:
                continue

            try:
                reviews = await self.scrape_reviews(
                    product_url,
                    max_reviews=config.scraper.max_reviews_per_product,
                )
            except Exception as exc:
                logger.error("Failed to get reviews for %s: %s", product_url, exc)
                reviews = []

            result_products.append({
                "product_url": product_url,
                "title": product.get("title", ""),
                "reviews": reviews,
            })
            total_reviews += len(reviews)
            logger.info("Collected %d reviews for product: %s", len(reviews), product.get("title", "")[:50])

        return {
            "shop_url": shop_url,
            "total_products": len(result_products),
            "total_reviews": total_reviews,
            "products": result_products,
        }

    async def close(self) -> None:
        """Close the underlying browser resources."""
        await self._scraper.close()

    async def __aenter__(self) -> "ReviewScraper":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
