"""
RankUp AI — Review Classifier
==============================

Uses the DeepSeek V4 Flash model to classify TikTok Shop product reviews
by sentiment (positive/negative/neutral) and urgency (high/medium/low),
with suggested actions for shop owners.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from openai import OpenAI, APIError, RateLimitError

from scraper.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah AI classifier untuk RankUp AI (TikTok Shop review analyzer).

TUGASAN:
Klasifikasi sentimen review TikTok Shop.

OUTPUT PER REVIEW:
- **Sentiment:** Positive / Negative / Neutral / Mixed
- **Confidence score:** 0-100% (seberapa yakin dengan klasifikasi)
- **Key issues/highlights:** 1-2 poin utama dari review
- **Recommended action:** Action yang harus diambil (terutama untuk negative)

PANDUAN SENTIMENT:
- **Positive:** Puas, antusias, rekomendasi, emoji senang (🔥✨💖)
- **Negative:** Kecewa, komplain, rusak, palsu, refund request
- **Neutral:** Biasa aja, tidak ada efek, pasrah
- **Mixed:** Ada positif DAN negatif (contoh: "produk oke, tapi pengiriman lama")

Return JSON untuk SATU review:
{
  "sentiment": "positive/negative/neutral/mixed",
  "confidence": 85,
  "key_issues": ["poin 1", "poin 2"],
  "recommended_action": "action yang disarankan"
}

Pastikan confidence score realistis (jangan selalu 100%)."""


class ReviewClassifier:
    """
    Classifies TikTok Shop reviews by sentiment and urgency using an LLM.

    Usage::

        classifier = ReviewClassifier()
        result = classifier.classify_review("This product is amazing!")
        results = classifier.classify_reviews_batch(reviews_list)
    """

    def __init__(self) -> None:
        if not config.llm.api_key:
            logger.warning("OPENAI_API_KEY not set. ReviewClassifier will fail.")
        self._client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout,
        )

    def classify_review(self, review_text: str) -> Dict[str, Any]:
        """
        Classify a single review.

        Args:
            review_text: The text content of the review.

        Returns:
            dict with keys: sentiment (str), urgency (str), suggested_action (str).

        Raises:
            ValueError: If review_text is empty.
            RuntimeError: If the LLM API call fails.
        """
        if not review_text or not review_text.strip():
            raise ValueError("review_text must not be empty")

        logger.debug("Classifying review (len=%d)", len(review_text))

        try:
            response = self._client.chat.completions.create(
                model=config.llm.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Classify this TikTok Shop review:\n\n\"{review_text}\"",
                    },
                ],
                temperature=0.1,  # low temperature for consistent classification
                max_tokens=1000,  # DeepSeek V4 Flash: ~700 tokens reasoning + 300 content
                response_format={"type": "json_object"},
            )
        except (APIError, RateLimitError) as exc:
            logger.error("LLM API error during review classification: %s", exc)
            raise RuntimeError(f"LLM API call failed: {exc}") from exc

        raw = response.choices[0].message.content or "{}"
        try:
            classification = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse classification: %s", exc)
            classification = {
                "sentiment": "neutral",
                "urgency": "low",
                "suggested_action": "Unable to classify — manual review recommended",
            }

        classification.setdefault("sentiment", "neutral")
        classification.setdefault("urgency", "low")
        classification.setdefault("suggested_action", "")
        classification["review_text"] = review_text

        logger.info(
            "Review classified: sentiment=%s, urgency=%s",
            classification["sentiment"],
            classification["urgency"],
        )
        return classification

    def classify_reviews_batch(
        self,
        reviews_list: List[Any],
    ) -> List[Dict[str, Any]]:
        """
        Classify a batch of reviews.

        Args:
            reviews_list: List of review items. Each item can be either:
                - a string (review text)
                - a dict with a "text" key

        Returns:
            List of classification dicts (same structure as :meth:`classify_review`).
        """
        results = []
        for item in reviews_list:
            if isinstance(item, str):
                text = item
            elif isinstance(item, dict):
                text = item.get("text", item.get("review_text", item.get("content", "")))
            else:
                text = str(item)

            try:
                results.append(self.classify_review(text))
            except Exception as exc:
                logger.error("Failed to classify review: %s", exc)
                results.append({
                    "sentiment": "neutral",
                    "urgency": "low",
                    "suggested_action": f"Classification error: {exc}",
                    "review_text": text,
                })
        return results
