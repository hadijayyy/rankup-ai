"""
RankUp AI — Pipeline Coordinator
=================================

Defines :class:`RankUpPipeline`, the main workflow coordinator that
executes the full RankUp AI pipeline: scrape → analyze → optimize →
dashboard update → report delivery.

Uses asyncio for parallel task execution where possible.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lazy imports from sibling packages (scraper, ai_engine, dashboard)
# ---------------------------------------------------------------------------

def _import_scraper():
    """Lazy-import the scraper package."""
    from scraper import TikTokScraper, ReviewScraper
    return TikTokScraper, ReviewScraper


def _import_ai_engine():
    """Lazy-import the ai_engine package."""
    from ai_engine import (
        ListingAnalyzer,
        ListingOptimizer,
        ReviewClassifier,
        ReplyDrafter,
        ReportGenerator,
    )
    return ListingAnalyzer, ListingOptimizer, ReviewClassifier, ReplyDrafter, ReportGenerator


def _import_dashboard():
    """Lazy-import the dashboard package."""
    from dashboard import SheetsManager, ReportFormatter, Notifier
    return SheetsManager, ReportFormatter, Notifier


def _import_client_manager():
    """Lazy-import the orchestrator's own ClientManager."""
    from .client_manager import ClientManager
    return ClientManager


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------

class RankUpPipeline:
    """Coordinates the end-to-end RankUp AI pipeline.

    Typical usage::

        pipeline = RankUpPipeline()
        result = await pipeline.run_full_pipeline("client-abc123")
        print(result["status"])

    The pipeline handles error recovery per-stage so that a failure in one
    phase does not abort the entire run.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_report_id(report_type: str = "weekly") -> str:
        """Generate a unique report ID."""
        return f"RPT-{report_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"

    @staticmethod
    def _now_iso() -> str:
        return datetime.utcnow().isoformat()

    @staticmethod
    def _period_dates(report_type: str) -> tuple[str, str]:
        """Return (start_date, end_date) ISO strings for the given period."""
        now = datetime.utcnow()
        if report_type == "daily":
            start = (now - timedelta(days=1)).isoformat()
            end = now.isoformat()
        elif report_type == "weekly":
            start = (now - timedelta(days=7)).isoformat()
            end = now.isoformat()
        elif report_type == "monthly":
            start = (now - timedelta(days=30)).isoformat()
            end = now.isoformat()
        else:
            start = (now - timedelta(days=7)).isoformat()
            end = now.isoformat()
        return start, end

    # ------------------------------------------------------------------
    # Stage 1: Scrape Listings & Reviews (parallel)
    # ------------------------------------------------------------------

    async def _scrape_stage(
        self,
        client_id: str,
        client_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Scrape listings and reviews in parallel.

        Args:
            client_id: The client identifier.
            client_config: Client configuration dict.

        Returns:
            Dict with ``listings`` and ``reviews`` keys.
        """
        TikTokScraper, ReviewScraper = _import_scraper()
        shop_url = client_config.get("tiktok_shop_url", "")
        review_limit = client_config.get("settings", {}).get("review_limit", 100)

        result: Dict[str, Any] = {"listings": [], "reviews": [], "errors": []}

        async def scrape_listings():
            try:
                scraper = TikTokScraper()
                listings = await scraper.scrape_shop_listings(shop_url)
                logger.info(
                    "Scraped %d listings for client %s", len(listings), client_id
                )
                return listings
            except Exception as exc:
                logger.error(
                    "Listing scrape failed for %s: %s", client_id, exc
                )
                result["errors"].append(f"listing_scrape: {exc}")
                return []

        async def scrape_reviews():
            try:
                scraper = ReviewScraper()
                reviews = await scraper.scrape_reviews(
                    shop_url, max_reviews=review_limit
                )
                logger.info(
                    "Scraped %d reviews for client %s", len(reviews), client_id
                )
                return reviews
            except Exception as exc:
                logger.error(
                    "Review scrape failed for %s: %s", client_id, exc
                )
                result["errors"].append(f"review_scrape: {exc}")
                return []

        listings_task = asyncio.create_task(scrape_listings())
        reviews_task = asyncio.create_task(scrape_reviews())

        # Wait for both to complete
        done, _ = await asyncio.wait(
            [listings_task, reviews_task],
            return_when=asyncio.ALL_COMPLETED,
        )

        for task in done:
            task_name = "listings" if task is listings_task else "reviews"
            try:
                data = task.result()
                result[task_name] = data
            except Exception as exc:
                logger.error(
                    "Unexpected error in %s scrape: %s", task_name, exc
                )
                result["errors"].append(f"{task_name}_scrape_exception: {exc}")

        return result

    # ------------------------------------------------------------------
    # Stage 2: Analyze Listings & Classify Reviews (parallel)
    # ------------------------------------------------------------------

    async def _analyze_stage(
        self,
        client_id: str,
        scrape_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze listings and classify reviews in parallel.

        Args:
            client_id: The client identifier.
            scrape_result: Output from :meth:`_scrape_stage`.

        Returns:
            Dict with ``analyzed_listings``, ``classified_reviews``,
            and ``draft_replies``.
        """
        (
            ListingAnalyzer,
            ListingOptimizer,
            ReviewClassifier,
            ReplyDrafter,
            _,
        ) = _import_ai_engine()

        raw_listings = scrape_result.get("listings", [])
        raw_reviews = scrape_result.get("reviews", [])

        result: Dict[str, Any] = {
            "analyzed_listings": [],
            "classified_reviews": [],
            "draft_replies": [],
            "errors": [],
        }

        async def analyze_listings():
            if not raw_listings:
                logger.info("No listings to analyze for %s", client_id)
                return [], []

            try:
                analyzer = ListingAnalyzer()
                optimizer = ListingOptimizer()
                analyzed = []
                for listing in raw_listings:
                    analysis = await analyzer.analyze(listing)
                    optimization = await optimizer.optimize(analysis)
                    analyzed.append({
                        **listing,
                        **analysis,
                        **optimization,
                    })
                logger.info(
                    "Analyzed and optimized %d listings for %s",
                    len(analyzed), client_id,
                )
                return analyzed
            except Exception as exc:
                logger.error(
                    "Listing analysis failed for %s: %s", client_id, exc
                )
                result["errors"].append(f"listing_analysis: {exc}")
                return [], []

        async def classify_reviews():
            if not raw_reviews:
                logger.info("No reviews to classify for %s", client_id)
                return [], []

            try:
                classifier = ReviewClassifier()
                drafter = ReplyDrafter()
                classified = []
                drafts = []
                for review in raw_reviews:
                    classification = await classifier.classify(review)
                    reply = await drafter.draft_reply(review, classification)
                    classified.append({**review, **classification})
                    drafts.append({
                        "review_id": review.get("review_id", ""),
                        "draft_reply": reply,
                    })
                logger.info(
                    "Classified %d reviews and drafted replies for %s",
                    len(classified), client_id,
                )
                return classified, drafts
            except Exception as exc:
                logger.error(
                    "Review classification failed for %s: %s", client_id, exc
                )
                result["errors"].append(f"review_classification: {exc}")
                return [], []

        listings_task = asyncio.create_task(analyze_listings())
        reviews_task = asyncio.create_task(classify_reviews())

        done, _ = await asyncio.wait(
            [listings_task, reviews_task],
            return_when=asyncio.ALL_COMPLETED,
        )

        for task in done:
            try:
                if task is listings_task:
                    analyzed, _ = task.result()
                    result["analyzed_listings"] = analyzed
                else:
                    classified, drafts = task.result()
                    result["classified_reviews"] = classified
                    result["draft_replies"] = drafts
            except Exception as exc:
                logger.error("Unexpected error in analyze stage: %s", exc)
                result["errors"].append(f"analyze_exception: {exc}")

        return result

    # ------------------------------------------------------------------
    # Stage 3: Generate report
    # ------------------------------------------------------------------

    async def _report_stage(
        self,
        client_id: str,
        client_config: Dict[str, Any],
        analyze_result: Dict[str, Any],
        report_type: str = "weekly",
    ) -> Dict[str, Any]:
        """Generate a report from analysis results.

        Args:
            client_id: The client identifier.
            client_config: Client configuration.
            analyze_result: Output from :meth:`_analyze_stage`.
            report_type: ``"daily"``, ``"weekly"``, or ``"monthly"``.

        Returns:
            Dict with report data ready for formatting and storage.
        """
        _, _, _, _, ReportGenerator = _import_ai_engine()

        analyzed_listings = analyze_result.get("analyzed_listings", [])
        classified_reviews = analyze_result.get("classified_reviews", [])
        start_date, end_date = self._period_dates(report_type)

        report_id = self._generate_report_id(report_type)

        # Calculate aggregate metrics
        total_listings = len(analyzed_listings)
        avg_score = (
            round(
                sum(
                    l.get("overall_score", 0) or 0
                    for l in analyzed_listings
                ) / total_listings,
                1,
            )
            if total_listings > 0
            else 0
        )

        total_reviews = len(classified_reviews)
        positive_reviews = sum(
            1 for r in classified_reviews if r.get("sentiment", "").lower() == "positive"
        )
        negative_reviews = sum(
            1 for r in classified_reviews if r.get("sentiment", "").lower() == "negative"
        )
        neutral_reviews = total_reviews - positive_reviews - negative_reviews

        # Listing breakdown for report
        listing_breakdown = []
        for listing in analyzed_listings:
            suggestions = listing.get("optimization_suggestions", "")
            if isinstance(suggestions, list):
                suggestions = "\n".join(suggestions)
            listing_breakdown.append({
                "product_name": listing.get("product_name", "Unknown"),
                "overall_score": listing.get("overall_score", "N/A"),
                "status": listing.get("status", ""),
                "suggestions": suggestions,
            })

        # Find top reviews
        top_positive = None
        top_negative = None
        for r in classified_reviews:
            if r.get("sentiment", "").lower() == "positive" and top_positive is None:
                top_positive = {
                    "text": r.get("review_text", ""),
                    "product": r.get("product_name", ""),
                    "date": r.get("date", ""),
                }
            if r.get("sentiment", "").lower() == "negative" and top_negative is None:
                top_negative = {
                    "text": r.get("review_text", ""),
                    "product": r.get("product_name", ""),
                    "date": r.get("date", ""),
                }

        # Generate summary
        summary = ""
        try:
            generator = ReportGenerator()
            summary = await generator.generate_summary({
                "client_name": client_config.get("name", "Client"),
                "total_listings": total_listings,
                "avg_listing_score": avg_score,
                "total_reviews": total_reviews,
                "positive_reviews": positive_reviews,
                "negative_reviews": negative_reviews,
                "neutral_reviews": neutral_reviews,
                "listing_breakdown": listing_breakdown,
            })
        except Exception as exc:
            logger.warning(
                "ReportGenerator summary failed for %s: %s", client_id, exc
            )
            summary = (
                f"Processed {total_listings} listings and {total_reviews} reviews. "
                f"Average listing score: {avg_score}. "
                f"Sentiment breakdown: {positive_reviews} positive, "
                f"{neutral_reviews} neutral, {negative_reviews} negative."
            )

        # Improvement actions
        improvement_actions = []
        for listing in analyzed_listings:
            suggestions = listing.get("optimization_suggestions", [])
            if isinstance(suggestions, str):
                suggestions = [s.strip() for s in suggestions.split("\n") if s.strip()]
            for s in suggestions[:3]:  # Top 3 per listing
                if s not in improvement_actions:
                    improvement_actions.append(s)

        report_data: Dict[str, Any] = {
            "report_id": report_id,
            "report_type": report_type,
            "client_name": client_config.get("name", "Client"),
            "client_id": client_id,
            "period_start": start_date,
            "period_end": end_date,
            "total_listings": total_listings,
            "avg_listing_score": avg_score,
            "listing_breakdown": listing_breakdown,
            "total_reviews": total_reviews,
            "positive_reviews": positive_reviews,
            "negative_reviews": negative_reviews,
            "neutral_reviews": neutral_reviews,
            "top_positive_review": top_positive,
            "top_negative_review": top_negative,
            "improvement_actions": improvement_actions[:10],
            "summary": summary,
        }

        logger.info(
            "Generated %s report %s for %s: %d listings, %d reviews",
            report_type, report_id, client_id, total_listings, total_reviews,
        )
        return report_data

    # ------------------------------------------------------------------
    # Stage 4: Update dashboard (Sheets)
    # ------------------------------------------------------------------

    async def _dashboard_stage(
        self,
        client_id: str,
        client_config: Dict[str, Any],
        analyze_result: Dict[str, Any],
        report_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update the Google Sheets dashboard with fresh data.

        Args:
            client_id: The client identifier.
            client_config: Client configuration.
            analyze_result: Output from :meth:`_analyze_stage`.
            report_data: Output from :meth:`_report_stage`.

        Returns:
            Dict with ``sheets_updated`` boolean and details.
        """
        SheetsManager, _, _ = _import_dashboard()
        sheets_id = client_config.get("sheets_id", "")

        if not sheets_id:
            logger.warning(
                "No sheets_id for client %s; skipping dashboard update.", client_id
            )
            return {"sheets_updated": False, "reason": "no_sheets_id"}

        result: Dict[str, Any] = {"sheets_updated": False, "details": {}}

        try:
            manager = SheetsManager()

            # Update listings
            analyzed = analyze_result.get("analyzed_listings", [])
            if analyzed:
                listing_count = manager.update_listing_data(sheets_id, analyzed)
                result["details"]["listings_written"] = listing_count

            # Update reviews
            classified = analyze_result.get("classified_reviews", [])
            if classified:
                # Inject draft replies
                drafts_map = {
                    d.get("review_id", ""): d.get("draft_reply", "")
                    for d in analyze_result.get("draft_replies", [])
                }
                for review in classified:
                    rid = review.get("review_id", "")
                    if rid in drafts_map:
                        review["draft_reply"] = drafts_map[rid]
                        review["reply_status"] = "drafted"

                review_count = manager.update_review_data(sheets_id, classified)
                result["details"]["reviews_written"] = review_count

            # Update report
            manager.update_report_data(sheets_id, report_data)
            result["details"]["report_appended"] = True

            result["sheets_updated"] = True
            logger.info(
                "Dashboard updated for client %s (sheet: %s)",
                client_id, sheets_id,
            )

        except Exception as exc:
            logger.error(
                "Dashboard update failed for %s: %s", client_id, exc
            )
            result["sheets_updated"] = False
            result["reason"] = str(exc)

        return result

    # ------------------------------------------------------------------
    # Stage 5: Send notifications
    # ------------------------------------------------------------------

    async def _notify_stage(
        self,
        client_config: Dict[str, Any],
        report_data: Dict[str, Any],
    ) -> Dict[str, bool]:
        """Send report notifications to the client.

        Args:
            client_config: Client configuration with email and phone.
            report_data: Output from :meth:`_report_stage`.

        Returns:
            Dict with delivery status per channel.
        """
        _, _, Notifier = _import_dashboard()
        email = client_config.get("email", "")
        phone = client_config.get("phone", "")
        settings = client_config.get("settings", {})
        notify_email = settings.get("notify_email", True)
        notify_whatsapp = settings.get("notify_whatsapp", False)

        status: Dict[str, bool] = {"email": False, "whatsapp": False}

        if not email and not phone:
            logger.warning("No contact info for client; skipping notifications.")
            return status

        try:
            notifier = Notifier()

            if email and notify_email:
                email_status = notifier.send_weekly_report(
                    client_email=email,
                    report_data=report_data,
                    phone=phone if notify_whatsapp else None,
                )
                status.update(email_status)
            elif phone and notify_whatsapp:
                # Send WhatsApp-only
                from .report_formatter import ReportFormatter
                wa_text = ReportFormatter.format_whatsapp_report(report_data)
                wa_ok = notifier.send_whatsapp(phone=phone, message=wa_text)
                status["whatsapp"] = wa_ok

            logger.info(
                "Notification delivery for %s: email=%s, whatsapp=%s",
                client_config.get("name", "Client"),
                status["email"],
                status["whatsapp"],
            )

        except Exception as exc:
            logger.error("Notification stage failed: %s", exc)

        return status

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    async def run_full_pipeline(
        self,
        client_id: str,
    ) -> Dict[str, Any]:
        """Execute the complete RankUp AI pipeline for a client.

        Stages executed in order (with parallel sub-tasks where noted):
          1. **Scrape** — listings and reviews (parallel)
          2. **Analyze** — analyze listings and classify reviews (parallel)
          3. **Report** — generate report data
          4. **Dashboard** — update Google Sheets
          5. **Notify** — send email/WhatsApp notifications

        Each stage is independent; a failure in one stage does not prevent
        later stages from running.

        Args:
            client_id: The unique client identifier.

        Returns:
            A dict summarizing pipeline execution:
            {
                "status": "complete" | "partial",
                "client_id": ...,
                "stages": {
                    "scrape": {"success": bool, ...},
                    "analyze": {"success": bool, ...},
                    "report": {"success": bool, ...},
                    "dashboard": {"success": bool, ...},
                    "notify": {"success": bool, ...},
                },
                "report_data": {...},
                "errors": [...]
            }
        """
        ClientManager = _import_client_manager()
        cm = ClientManager()
        client_config = cm.get_client(client_id)

        if client_config is None:
            return {
                "status": "error",
                "client_id": client_id,
                "error": f"Client '{client_id}' not found.",
                "stages": {},
            }

        logger.info(
            "Starting full pipeline for client '%s' (%s)",
            client_config.get("name", client_id), client_id,
        )

        pipeline_result: Dict[str, Any] = {
            "status": "complete",
            "client_id": client_id,
            "stages": {},
            "report_data": None,
            "errors": [],
        }

        # Stage 1: Scrape
        scrape_result = await self._scrape_stage(client_id, client_config)
        scrape_ok = len(scrape_result.get("errors", [])) == 0
        pipeline_result["stages"]["scrape"] = {
            "success": scrape_ok,
            "listings_count": len(scrape_result.get("listings", [])),
            "reviews_count": len(scrape_result.get("reviews", [])),
            "errors": scrape_result.get("errors", []),
        }
        if not scrape_ok:
            pipeline_result["errors"].extend(scrape_result.get("errors", []))

        # Stage 2: Analyze
        analyze_result = await self._analyze_stage(client_id, scrape_result)
        analyze_ok = len(analyze_result.get("errors", [])) == 0
        pipeline_result["stages"]["analyze"] = {
            "success": analyze_ok,
            "listings_analyzed": len(analyze_result.get("analyzed_listings", [])),
            "reviews_classified": len(analyze_result.get("classified_reviews", [])),
            "errors": analyze_result.get("errors", []),
        }
        if not analyze_ok:
            pipeline_result["errors"].extend(analyze_result.get("errors", []))

        # Stage 3: Report
        report_data = None
        report_ok = False
        try:
            report_data = await self._report_stage(
                client_id, client_config, analyze_result, "weekly"
            )
            report_ok = True
        except Exception as exc:
            logger.error("Report generation failed: %s", exc)
            pipeline_result["errors"].append(f"report_generation: {exc}")
        pipeline_result["stages"]["report"] = {
            "success": report_ok,
            "report_id": report_data.get("report_id") if report_data else None,
        }
        if report_data:
            pipeline_result["report_data"] = report_data

        # Stage 4: Dashboard
        dashboard_result = {}
        if report_data:
            dashboard_result = await self._dashboard_stage(
                client_id, client_config, analyze_result, report_data,
            )
        pipeline_result["stages"]["dashboard"] = {
            "success": dashboard_result.get("sheets_updated", False),
            "details": dashboard_result.get("details", {}),
        }

        # Stage 5: Notify
        notify_result = {}
        if report_data:
            notify_result = await self._notify_stage(client_config, report_data)
        pipeline_result["stages"]["notify"] = {
            "success": notify_result.get("email", False) or notify_result.get("whatsapp", False),
            "email_sent": notify_result.get("email", False),
            "whatsapp_sent": notify_result.get("whatsapp", False),
        }

        # Determine overall status
        all_stages_ok = all(
            s.get("success", False)
            for s in pipeline_result["stages"].values()
        )
        pipeline_result["status"] = "complete" if all_stages_ok else "partial"

        logger.info(
            "Pipeline finished for %s — status: %s",
            client_id, pipeline_result["status"],
        )
        return pipeline_result

    # ------------------------------------------------------------------
    # Daily pipeline (review monitoring only)
    # ------------------------------------------------------------------

    async def run_daily_pipeline(self, client_id: str) -> Dict[str, Any]:
        """Run a lightweight daily pipeline focused on review monitoring.

        Stages:
          1. Scrape reviews only
          2. Classify reviews and draft replies
          3. Update Reviews tab in Sheets
          4. Send alert if negative reviews exceed threshold

        Args:
            client_id: The unique client identifier.

        Returns:
            A summary dict with stage results.
        """
        ClientManager = _import_client_manager()
        cm = ClientManager()
        client_config = cm.get_client(client_id)

        if client_config is None:
            return {
                "status": "error",
                "client_id": client_id,
                "error": f"Client '{client_id}' not found.",
            }

        logger.info(
            "Starting daily pipeline for '%s' (%s)",
            client_config.get("name", client_id), client_id,
        )

        _, ReviewScraper = _import_scraper()
        _, _, ReviewClassifier, ReplyDrafter, _ = _import_ai_engine()
        SheetsManager, _, Notifier = _import_dashboard()

        result: Dict[str, Any] = {
            "status": "complete",
            "client_id": client_id,
            "stages": {},
            "errors": [],
        }

        shop_url = client_config.get("tiktok_shop_url", "")
        review_limit = client_config.get("settings", {}).get("review_limit", 100)
        sheets_id = client_config.get("sheets_id", "")

        # --- Scrape reviews ---
        reviews = []
        try:
            scraper = ReviewScraper()
            reviews = await scraper.scrape_reviews(shop_url, max_reviews=review_limit)
            result["stages"]["scrape"] = {
                "success": True,
                "reviews_count": len(reviews),
            }
            logger.info("Daily scrape: %d reviews for %s", len(reviews), client_id)
        except Exception as exc:
            logger.error("Daily scrape failed for %s: %s", client_id, exc)
            result["stages"]["scrape"] = {"success": False, "error": str(exc)}
            result["errors"].append(f"daily_scrape: {exc}")
            result["status"] = "partial"
            return result

        # --- Classify & draft ---
        classified = []
        drafts = []
        try:
            classifier = ReviewClassifier()
            drafter = ReplyDrafter()
            for review in reviews:
                classification = await classifier.classify(review)
                reply = await drafter.draft_reply(review, classification)
                classified.append({**review, **classification})
                drafts.append({
                    "review_id": review.get("review_id", ""),
                    "draft_reply": reply,
                })
            result["stages"]["classify"] = {
                "success": True,
                "classified_count": len(classified),
            }
        except Exception as exc:
            logger.error("Daily classify failed: %s", exc)
            result["stages"]["classify"] = {"success": False, "error": str(exc)}
            result["errors"].append(f"daily_classify: {exc}")

        # --- Update Sheets ---
        if sheets_id and classified:
            try:
                manager = SheetsManager()
                # Attach drafts
                drafts_map = {d["review_id"]: d["draft_reply"] for d in drafts}
                for r in classified:
                    rid = r.get("review_id", "")
                    if rid in drafts_map:
                        r["draft_reply"] = drafts_map[rid]
                        r["reply_status"] = "drafted"
                manager.update_review_data(sheets_id, classified)
                result["stages"]["dashboard"] = {"success": True}
            except Exception as exc:
                logger.error("Daily dashboard update failed: %s", exc)
                result["stages"]["dashboard"] = {"success": False, "error": str(exc)}
                result["errors"].append(f"daily_dashboard: {exc}")

        # --- Alert on negative reviews ---
        negative_count = sum(
            1 for r in classified if r.get("sentiment", "").lower() == "negative"
        )
        if negative_count >= 3:
            try:
                email = client_config.get("email", "")
                if email:
                    notifier = Notifier()
                    alert_subject = (
                        f"RankUp AI Alert — {negative_count} negative reviews "
                        f"for {client_config.get('name', 'Client')}"
                    )
                    alert_html = f"""
                    <html><body>
                    <h2>⚠️ Negative Review Alert</h2>
                    <p>We detected <strong>{negative_count}</strong> negative reviews in
                    the last 24 hours for {client_config.get('name', 'Client')}.</p>
                    <p>Please review them in your RankUp AI dashboard and take action.</p>
                    </body></html>
                    """
                    notifier.send_email(to=email, subject=alert_subject, html_body=alert_html)
                    result["stages"]["alert"] = {"success": True, "negative_count": negative_count}
                    logger.info("Alert sent for %d negative reviews", negative_count)
            except Exception as exc:
                logger.error("Daily alert failed: %s", exc)
                result["stages"]["alert"] = {"success": False, "error": str(exc)}

        return result

    # ------------------------------------------------------------------
    # Weekly pipeline
    # ------------------------------------------------------------------

    async def run_weekly_pipeline(self, client_id: str) -> Dict[str, Any]:
        """Run the full weekly pipeline (scrape → analyze → report → notify).

        This is a convenience wrapper around :meth:`run_full_pipeline`
        that forces report_type to ``"weekly"``.

        Args:
            client_id: The unique client identifier.

        Returns:
            Full pipeline result dict.
        """
        return await self.run_full_pipeline(client_id)


__all__ = ["RankUpPipeline"]
