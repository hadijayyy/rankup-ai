"""
RankUp AI — Reply Drafter
==========================

Uses the DeepSeek V4 Flash model to draft empathetic, on-brand replies
to TikTok Shop reviews. Adapts tone based on sentiment and product context.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from openai import OpenAI, APIError, RateLimitError

from scraper.config import config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah AI reply drafter untuk RankUp AI (TikTok Shop review management).

TUGASAN:
Draft reply untuk review TikTok Shop.

ATURAN:
1. **Tone:** Empathetic, professional, human-like
2. **Panjang:** 50-100 karakter per reply (PENTING! Jangan lebih dari 100!)
3. **Emoji:** Gunakan yang tepat (🙏😊✨🫶🙌), jangan berlebihan
4. **Bahasa Indonesia:** Casual, natural, seperti CS yang ramah

POLA REPLY:
- **Negative:** Empati + solusi (ganti/rugi) + janji perbaikan
- **Positive:** Apresiasi + CTA (repurchase/bundling) + ajakan share
- **Mixed:** Apresiasi + maaf + follow-up/solusi

Return JSON:
{
  "reply_text": "teks reply (50-100 char)",
  "tone": "empathetic/professional/friendly",
  "star_rating_suggestion": 1-5 (rating yang disarankan untuk review ini),
  "follow_up_needed": true/false
}

CONTOH:
- Negative (barang pecah): "Maaf banget barang pecah 🙏 Segera DM admin ya, kami ganti gratis! 😊"
- Positive (puas): "Makasih kak! Seneng serumnya cocok ✨ Jangan lupa repurchase ya! 🫶"
- Mixed (produk oke, pengiriman lama): "Makasih reviewnya! Maaf lama kirim, kami koordinasi sama kurir 😊"

PENTING: Reply harus SINGKAT (maks 100 karakter)!"""


class ReplyDrafter:
    """
    Drafts replies to TikTok Shop reviews using an LLM.

    Usage::

        drafter = ReplyDrafter()
        reply = drafter.draft_reply(review_data, sentiment="negative", product_info={...})
    """

    def __init__(self) -> None:
        if not config.llm.api_key:
            logger.warning("OPENAI_API_KEY not set. ReplyDrafter will fail.")
        self._client = OpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            timeout=config.llm.timeout,
        )

    def draft_reply(
        self,
        review_data: Dict[str, Any],
        sentiment: Optional[str] = None,
        product_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Draft a reply to a product review.

        Args:
            review_data: dict with keys (reviewer_name, rating, text, date, helpful_count)
                or at minimum a "text" key.
            sentiment: Optional override ("positive", "negative", "neutral").
                If None, the function infers from the review_data or defaults to "neutral".
            product_info: Optional dict with product details (title, price, etc.)
                to personalise the reply.

        Returns:
            dict with keys:
                reply_text (str), tone (str), follow_up_needed (bool).

        Raises:
            ValueError: If review_data is empty.
            RuntimeError: If the LLM API call fails.
        """
        if not review_data:
            raise ValueError("review_data must not be empty")

        # Build context
        text = review_data.get("text", review_data.get("review_text", ""))
        rating = review_data.get("rating", 0)
        reviewer = review_data.get("reviewer_name", review_data.get("reviewer", "Customer"))

        # Determine sentiment if not provided
        if sentiment is None:
            if rating >= 4:
                sentiment = "positive"
            elif rating <= 2:
                sentiment = "negative"
            else:
                sentiment = "neutral"

        product_context = ""
        if product_info:
            product_context = (
                f"Product: {product_info.get('title', 'N/A')}\n"
                f"Price: {product_info.get('price', 'N/A')}\n"
            )

        prompt = (
            f"Review by {reviewer} (rating: {rating}/5, sentiment: {sentiment}):\n"
            f"\"{text}\"\n\n"
            f"{product_context}\n"
            f"Draft a {sentiment}-appropriate reply."
        )

        logger.info(
            "Drafting reply for sentiment=%s, reviewer=%s", sentiment, reviewer
        )

        try:
            response = self._client.chat.completions.create(
                model=config.llm.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for consistent, professional replies
                max_tokens=800,  # DeepSeek V4 Flash: ~600 tokens reasoning + 200 content
                response_format={"type": "json_object"},
            )
        except (APIError, RateLimitError) as exc:
            logger.error("LLM API error during reply drafting: %s", exc)
            raise RuntimeError(f"LLM API call failed: {exc}") from exc

        raw = response.choices[0].message.content or "{}"
        try:
            reply = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse reply draft: %s", exc)
            reply = {
                "reply_text": f"Thank you for your review, {reviewer}. We appreciate your feedback and will use it to improve.",
                "tone": "professional",
                "follow_up_needed": False,
            }

        reply.setdefault("reply_text", "")
        reply.setdefault("tone", "professional")
        reply.setdefault("follow_up_needed", False)

        logger.info(
            "Reply drafted — tone=%s, follow_up_needed=%s, length=%d",
            reply["tone"], reply["follow_up_needed"], len(reply.get("reply_text", "")),
        )
        return reply

    def draft_replies_batch(
        self,
        reviews: list,
        product_info: Optional[Dict[str, Any]] = None,
    ) -> list:
        """
        Draft replies for multiple reviews.

        Args:
            reviews: List of review dicts (each with at least "text").
            product_info: Optional product details for personalisation.

        Returns:
            List of reply dicts.
        """
        results = []
        for review in reviews:
            sentiment = None
            if isinstance(review, dict):
                sentiment = review.get("sentiment", None)
            try:
                results.append(self.draft_reply(review, sentiment=sentiment, product_info=product_info))
            except Exception as exc:
                logger.error("Failed to draft reply: %s", exc)
                results.append({
                    "reply_text": f"Thank you for your review. We appreciate your feedback.",
                    "tone": "professional",
                    "follow_up_needed": False,
                })
        return results
