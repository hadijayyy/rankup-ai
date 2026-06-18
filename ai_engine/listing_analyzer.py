"""
RankUp AI — Listing Analyzer
=============================

Uses the DeepSeek V4 Flash model (OpenAI-compatible API) to analyze
TikTok Shop product listings and produce a structured analysis with
scores, weaknesses, strengths, and recommendations.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from openai import OpenAI, APIError, RateLimitError

from scraper.config import config

logger = logging.getLogger(__name__)

# System prompt for listing analysis
SYSTEM_PROMPT = """You are a TikTok Shop listing optimization expert. Your task is to analyze product listings
and provide actionable feedback. TikTok Shop has a fast-paced, visually-driven environment where
listings need to be short, catchy, and optimized for mobile viewing.

Analyze the product listing data and return a JSON object with the following fields:
- "score": integer from 1 to 10 (10 = perfect listing)
- "weaknesses": array of strings describing specific issues found
- "strengths": array of strings describing what the listing does well
- "recommendations": array of specific, actionable recommendations to improve the listing

Be thorough and specific. Consider:
- Title quality (keywords, length, catchiness)
- Description quality (detail, formatting, persuasion)
- Hashtag usage and relevance
- Pricing presentation
- Visual appeal (image quality from available data)
- Sales and social proof elements
- Mobile optimization
- TikTok style (emoji usage, conversational tone, trends)"""


class ListingAnalyzer:
    """
    Analyzes TikTok Shop product listings using an LLM.

    Usage::

        analyzer = ListingAnalyzer()
        result = await analyzer.analyze_listing(product_data)
        print(result["score"], result["recommendations"])
    """

    def __init__(self) -> None:
        if not config.llm.api_key:
            logger.warning(
                "OPENAI_API_KEY is not set. ListingAnalyzer will fail on calls."
            )
        self._client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout,
        )

    def analyze_listing(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single product listing and return a structured analysis.

        Args:
            product_data: dict with keys (title, description, price, images,
                hashtags, sales_count, rating, review_count, url).

        Returns:
            dict with keys:
                score (int 1-10), weaknesses (list[str]), strengths (list[str]),
                recommendations (list[str]), raw_product_data (dict).

        Raises:
            ValueError: If product_data is empty.
            RuntimeError: If the LLM API call fails.
        """
        if not product_data:
            raise ValueError("product_data must not be empty")

        # Build a condensed listing description for the LLM
        listing_text = self._format_listing(product_data)
        logger.info("Analyzing listing: %s", product_data.get("title", "Untitled")[:60])

        try:
            response = self._client.chat.completions.create(
                model=config.llm.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Please analyze this TikTok Shop product listing:\n\n{listing_text}",
                    },
                ],
                temperature=config.llm.temperature,
                max_tokens=2500,  # DeepSeek V4 Flash: ~1500 reasoning + 1000 content for detailed analysis
                response_format={"type": "json_object"},
            )
        except (APIError, RateLimitError) as exc:
            logger.error("LLM API error during listing analysis: %s", exc)
            raise RuntimeError(f"LLM API call failed: {exc}") from exc

        raw = response.choices[0].message.content or "{}"
        try:
            analysis = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse LLM response: %s", exc)
            analysis = {
                "score": 5,
                "weaknesses": ["Unable to parse analysis"],
                "strengths": [],
                "recommendations": ["Try again later"],
            }

        # Ensure all expected keys exist
        analysis.setdefault("score", 5)
        analysis.setdefault("weaknesses", [])
        analysis.setdefault("strengths", [])
        analysis.setdefault("recommendations", [])
        analysis["raw_product_data"] = product_data

        logger.info(
            "Analysis complete: score=%d, %d weaknesses, %d recommendations",
            analysis["score"],
            len(analysis["weaknesses"]),
            len(analysis["recommendations"]),
        )
        return analysis

    def analyze_listings_batch(
        self, products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple listings.

        Args:
            products: List of product data dicts.

        Returns:
            List of analysis dicts (same structure as :meth:`analyze_listing`).
        """
        results = []
        for product in products:
            try:
                results.append(self.analyze_listing(product))
            except Exception as exc:
                logger.error("Failed to analyze listing: %s", exc)
                results.append({
                    "score": 0,
                    "weaknesses": [f"Analysis error: {exc}"],
                    "strengths": [],
                    "recommendations": [],
                    "raw_product_data": product,
                })
        return results

    @staticmethod
    def _format_listing(product_data: Dict[str, Any]) -> str:
        """Format product data into a readable text block for the LLM."""
        lines = [
            f"Title: {product_data.get('title', 'N/A')}",
            f"Description: {product_data.get('description', 'N/A')}",
            f"Price: {product_data.get('price', 'N/A')}",
            f"Rating: {product_data.get('rating', 'N/A')} / 5",
            f"Sales count: {product_data.get('sales_count', 0)}",
            f"Review count: {product_data.get('review_count', 0)}",
            f"Hashtags: {', '.join(product_data.get('hashtags', [])) or 'None'}",
            f"Number of images: {len(product_data.get('images', []))}",
        ]
        return "\n".join(lines)
