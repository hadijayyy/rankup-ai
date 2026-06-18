"""
RankUp AI — Report Generator
=============================

Uses the DeepSeek V4 Flash model to generate weekly intelligence reports
for TikTok Shop sellers. Combines listing scores, review summaries,
competitor insights, and action items into a formatted markdown report.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from openai import OpenAI, APIError, RateLimitError

from scraper.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a TikTok Shop intelligence analyst. You generate weekly performance reports
for sellers that are clear, actionable, and data-driven.

Given the seller's product data, listing analyses, and review information,
produce a JSON report with these fields:
- "summary": 2-3 sentence executive summary of the week's performance
- "listing_scores": array of {"title": str, "score": int} for each listing
- "review_summary": object with:
    "total_reviews": int,
    "positive_percent": float,
    "negative_percent": float,
    "neutral_percent": float,
    "top_issues": array of str (most common complaints),
    "top_praises": array of str (most common compliments)
- "competitor_insights": array of str (insights about competition / market trends)
- "action_items": array of str (3-5 prioritized action items)
- "formatted_report": a complete markdown report string for the seller,
  with sections for Overview, Listing Performance, Review Summary,
  Competitor Insights, and Action Items. Use headers, bold, bullet points.
  Make it look professional and readable."""


class ReportGenerator:
    """
    Generates weekly intelligence reports for TikTok Shop sellers.

    Usage::

        generator = ReportGenerator()
        report = generator.generate_weekly_report(client_data)
        print(report["formatted_report"])
    """

    def __init__(self) -> None:
        if not config.llm.api_key:
            logger.warning("OPENAI_API_KEY not set. ReportGenerator will fail.")
        self._client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout,
        )

    def generate_weekly_report(
        self,
        client_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive weekly performance report.

        Args:
            client_data: dict with the following structure::

                {
                    "shop_name": str,
                    "shop_url": str,
                    "week_start": str (ISO date),
                    "week_end": str (ISO date),
                    "listings": [
                        {
                            "title": str,
                            "url": str,
                            "score": int (1-10),
                            "reviews": [
                                {"text": str, "rating": float, "date": str, ...}
                            ],
                            "sales_count": int,
                            "rating": float,
                            "review_count": int,
                        }
                    ],
                    "competitor_mentions": [str],  # optional
                    "previous_score": float,  # optional, for trend
                }

        Returns:
            dict with keys:
                summary (str), listing_scores (list[dict]),
                review_summary (dict), competitor_insights (list[str]),
                action_items (list[str]), formatted_report (str).

        Raises:
            ValueError: If client_data is empty.
            RuntimeError: If the LLM API call fails.
        """
        if not client_data:
            raise ValueError("client_data must not be empty")

        # Compute basic stats before sending to LLM
        listings = client_data.get("listings", [])
        all_reviews = []
        for listing in listings:
            all_reviews.extend(listing.get("reviews", []))

        total_reviews = len(all_reviews)
        if total_reviews > 0:
            positive = sum(1 for r in all_reviews if r.get("rating", 0) >= 4)
            negative = sum(1 for r in all_reviews if r.get("rating", 0) <= 2)
            neutral = total_reviews - positive - negative
            pos_pct = round(positive / total_reviews * 100, 1)
            neg_pct = round(negative / total_reviews * 100, 1)
            neu_pct = round(neutral / total_reviews * 100, 1)
        else:
            pos_pct = neg_pct = neu_pct = 0.0

        avg_score = 0.0
        if listings:
            scores = [l.get("score", 0) for l in listings if l.get("score")]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        # Enrich client data with computed stats
        enriched_data = {
            **client_data,
            "total_listings": len(listings),
            "total_reviews": total_reviews,
            "average_listing_score": avg_score,
            "positive_review_pct": pos_pct,
            "negative_review_pct": neg_pct,
            "neutral_review_pct": neu_pct,
        }

        data_json = json.dumps(enriched_data, indent=2, default=str)

        logger.info(
            "Generating weekly report for shop=%s | listings=%d | reviews=%d",
            client_data.get("shop_name", "Unknown"),
            len(listings),
            total_reviews,
        )

        try:
            response = self._client.chat.completions.create(
                model=config.llm.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Generate a weekly TikTok Shop intelligence report for the seller "
                            f"based on this data:\n\n```json\n{data_json}\n```"
                        ),
                    },
                ],
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
                response_format={"type": "json_object"},
            )
        except (APIError, RateLimitError) as exc:
            logger.error("LLM API error during report generation: %s", exc)
            raise RuntimeError(f"LLM API call failed: {exc}") from exc

        raw = response.choices[0].message.content or "{}"
        try:
            report = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse report JSON: %s", exc)
            report = {
                "summary": "Report generation failed due to a parsing error.",
                "listing_scores": [],
                "review_summary": {
                    "total_reviews": total_reviews,
                    "positive_percent": pos_pct,
                    "negative_percent": neg_pct,
                    "neutral_percent": neu_pct,
                    "top_issues": [],
                    "top_praises": [],
                },
                "competitor_insights": [],
                "action_items": ["Regenerate report"],
                "formatted_report": "# Weekly Report\n\nReport generation encountered an error. Please try again.",
            }

        # Ensure all keys exist
        report.setdefault("summary", "")
        report.setdefault("listing_scores", [])
        report.setdefault("review_summary", {})
        report.setdefault("competitor_insights", [])
        report.setdefault("action_items", [])
        report.setdefault("formatted_report", "")

        # Fallback for formatted_report
        if not report.get("formatted_report"):
            report["formatted_report"] = self._build_fallback_report(
                client_data, report
            )

        logger.info("Report generated successfully — %d action items", len(report.get("action_items", [])))
        return report

    @staticmethod
    def _build_fallback_report(
        client_data: Dict[str, Any], report: Dict[str, Any]
    ) -> str:
        """Build a minimal markdown report when the LLM doesn't produce one."""
        shop_name = client_data.get("shop_name", "Your Shop")
        lines = [
            f"# 📊 Weekly Report — {shop_name}",
            "",
            f"**Summary:** {report.get('summary', 'No summary available.')}",
            "",
            "## 📈 Listing Performance",
        ]
        for ls in report.get("listing_scores", []):
            title = ls.get("title", "Unknown")
            score = ls.get("score", "N/A")
            bars = "⭐" * (score if isinstance(score, int) and score > 0 else 0)
            lines.append(f"- **{title}**: {score}/10 {bars}")

        rs = report.get("review_summary", {})
        lines.extend([
            "",
            "## 💬 Review Summary",
            f"- Total reviews: {rs.get('total_reviews', 0)}",
            f"- Positive: {rs.get('positive_percent', 0)}%",
            f"- Negative: {rs.get('negative_percent', 0)}%",
            f"- Neutral: {rs.get('neutral_percent', 0)}%",
        ])

        if report.get("action_items"):
            lines.extend(["", "## ✅ Action Items"])
            for item in report["action_items"]:
                lines.append(f"- {item}")

        return "\n".join(lines)
