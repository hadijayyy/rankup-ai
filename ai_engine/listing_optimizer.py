"""
RankUp AI — Listing Optimizer
==============================

Uses the DeepSeek V4 Flash model to generate optimized TikTok Shop
listings from existing product data and analysis. Maintains TikTok's
short, catchy, emoji-friendly style.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI, APIError, RateLimitError

from scraper.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah AI optimizer untuk RankUp AI (TikTok Shop listing optimizer).

TUGASAN:
Generate versi optimized dari listing TikTok Shop.

ATURAN WAJIB:
1. **Judul (Title):** Maks 80 karakter, keyword-rich, punchy
2. **Deskripsi:** 150-250 karakter, emotional + benefit-driven
3. **Bullet Points:** 3 fitur utama dengan emoji
4. **Emoji:** Gunakan yang relevan (✨, 💖, 😍, 🧴, 🔥, dll)
5. **Urgency/Scarcity:** "Stok terbatas", "Limited Edition", "Habis dalam X hari"
6. **Social Proof:** Angka penjualan atau testimoni (contoh: "10.000+ terjual")
7. **Call-to-Action:** "Checkout sekarang!", "Buruan sebelum sold out!"
8. **Bahasa Indonesia:** Casual tapi profesional, target market Indonesia female 18-35

Return JSON dengan field:
- "optimized_title": judul baru (string, maks 80 char)
- "optimized_description": deskripsi baru (string, 150-250 char)
- "bullet_points": array 3 string (fitur utama dengan emoji)
- "optimized_hashtags": array 3-5 hashtag strings
- "changes_made": array penjelasan perubahan
- "expected_impact": string dampak yang diharapkan"""


class ListingOptimizer:
    """
    Optimizes TikTok Shop product listings using an LLM.

    Usage::

        optimizer = ListingOptimizer()
        result = await optimizer.optimize_listing(product_data, analysis)
    """

    def __init__(self) -> None:
        if not config.llm.api_key:
            logger.warning("OPENAI_API_KEY not set. ListingOptimizer will fail.")
        self._client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout,
        )

    def optimize_listing(
        self,
        product_data: Dict[str, Any],
        analysis: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an optimized version of the product listing.

        Args:
            product_data: Original product data dict (title, description,
                hashtags, price, etc.).
            analysis: Optional analysis dict from :class:`ListingAnalyzer`.
                If provided, recommendations from the analysis are included
                in the prompt so the LLM can address them.

        Returns:
            dict with keys:
                optimized_title (str), optimized_description (str),
                optimized_hashtags (list[str]), changes_made (list[str]),
                expected_impact (str).

        Raises:
            ValueError: If product_data is empty.
            RuntimeError: If the LLM API call fails.
        """
        if not product_data:
            raise ValueError("product_data must not be empty")

        listing_text = self._format_listing(product_data)
        if analysis:
            listing_text += "\n\nPrevious analysis:\n"
            listing_text += f"Score: {analysis.get('score', 'N/A')}/10\n"
            listing_text += "Recommendations:\n"
            for rec in analysis.get("recommendations", []):
                listing_text += f"- {rec}\n"

        logger.info(
            "Optimizing listing: %s", product_data.get("title", "Untitled")[:60]
        )

        try:
            response = self._client.chat.completions.create(
                model=config.llm.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Please optimize this TikTok Shop product listing:\n\n{listing_text}",
                    },
                ],
                temperature=config.llm.temperature,
                max_tokens=2500,  # DeepSeek V4 Flash: ~1500 reasoning + 1000 content for optimized output
                response_format={"type": "json_object"},
            )
        except (APIError, RateLimitError) as exc:
            logger.error("LLM API error during listing optimization: %s", exc)
            raise RuntimeError(f"LLM API call failed: {exc}") from exc

        raw = response.choices[0].message.content or "{}"
        try:
            optimized = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM optimization response: %s", exc)
            optimized = {
                "optimized_title": product_data.get("title", ""),
                "optimized_description": product_data.get("description", ""),
                "optimized_hashtags": product_data.get("hashtags", []),
                "changes_made": ["Failed to optimize — using original"],
                "expected_impact": "None (optimization failed)",
            }

        optimized.setdefault("optimized_title", product_data.get("title", ""))
        optimized.setdefault("optimized_description", product_data.get("description", ""))
        optimized.setdefault("optimized_hashtags", product_data.get("hashtags", []))
        optimized.setdefault("changes_made", [])
        optimized.setdefault("expected_impact", "")

        logger.info("Optimization complete — title length: %d", len(optimized.get("optimized_title", "")))
        return optimized

    def optimize_listings_batch(
        self,
        products: List[Dict[str, Any]],
        analyses: Optional[List[Optional[Dict[str, Any]]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Optimize multiple listings.

        Args:
            products: List of product data dicts.
            analyses: Optional list of analysis dicts (one per product, or None).

        Returns:
            List of optimization result dicts.
        """
        results = []
        for i, product in enumerate(products):
            analysis = analyses[i] if analyses and i < len(analyses) else None
            try:
                results.append(self.optimize_listing(product, analysis))
            except Exception as exc:
                logger.error("Failed to optimize listing %d: %s", i, exc)
                results.append({
                    "optimized_title": product.get("title", ""),
                    "optimized_description": product.get("description", ""),
                    "optimized_hashtags": product.get("hashtags", []),
                    "changes_made": [f"Optimization error: {exc}"],
                    "expected_impact": "None",
                })
        return results

    @staticmethod
    def _format_listing(product_data: Dict[str, Any]) -> str:
        lines = [
            f"Title: {product_data.get('title', 'N/A')}",
            f"Description: {product_data.get('description', 'N/A')}",
            f"Price: {product_data.get('price', 'N/A')}",
            f"Rating: {product_data.get('rating', 'N/A')} / 5",
            f"Sales count: {product_data.get('sales_count', 0)}",
            f"Review count: {product_data.get('review_count', 0)}",
            f"Current hashtags: {', '.join(product_data.get('hashtags', [])) or 'None'}",
        ]
        return "\n".join(lines)
