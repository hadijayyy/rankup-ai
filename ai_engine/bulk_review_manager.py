"""
RankUp AI — Bulk Review Manager
================================

Manages bulk review classification, alerts, and dashboard
for TikTok Shop sellers.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from .review_classifier import ReviewClassifier
from .reply_drafter import ReplyDrafter

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BulkReviewManager:
    """
    Manages bulk review operations for TikTok Shop sellers.
    
    Features:
    - Bulk review classification
    - Alert system for negative reviews
    - Dashboard data generation
    - Report generation
    """
    
    def __init__(self):
        self.classifier = ReviewClassifier()
        self.drafter = ReplyDrafter()
        self._reviews_cache: List[Dict[str, Any]] = []
        
    def classify_bulk_reviews(
        self, 
        reviews: List[str],
        product_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classify multiple reviews in bulk.
        
        Args:
            reviews: List of review texts
            product_info: Optional product context
            
        Returns:
            Dict with classifications, stats, and alerts
        """
        if not reviews:
            return {"reviews": [], "stats": {}, "alerts": []}
        
        logger.info("Classifying %d reviews in bulk", len(reviews))
        
        classifications = []
        alerts = []
        
        for i, review in enumerate(reviews):
            try:
                # Classify review
                result = self.classifier.classify_review(review)
                
                # Generate reply
                review_data = {
                    "text": review,
                    "rating": 3,  # Default neutral
                    "sentiment": result.get("sentiment", "neutral")
                }
                reply_result = self.drafter.draft_reply(
                    review_data, 
                    product_info=product_info
                )
                
                # Combine results
                combined = {
                    "id": i + 1,
                    "text": review,
                    "sentiment": result.get("sentiment", "neutral"),
                    "confidence": result.get("confidence", 0),
                    "key_issues": result.get("key_issues", []),
                    "recommended_action": result.get("recommended_action", ""),
                    "reply_text": reply_result.get("reply_text", ""),
                    "reply_tone": reply_result.get("tone", "professional"),
                    "analyzed_at": datetime.now().isoformat()
                }
                
                classifications.append(combined)
                
                # Generate alerts for critical reviews
                alert = self._check_alert(combined)
                if alert:
                    alerts.append(alert)
                    
            except Exception as exc:
                logger.error("Failed to classify review %d: %s", i, exc)
                classifications.append({
                    "id": i + 1,
                    "text": review,
                    "sentiment": "error",
                    "error": str(exc)
                })
        
        # Generate statistics
        stats = self._calculate_stats(classifications)
        
        # Cache reviews
        self._reviews_cache = classifications
        
        return {
            "reviews": classifications,
            "stats": stats,
            "alerts": alerts,
            "total_reviews": len(reviews),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _check_alert(self, classification: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if review needs alert."""
        sentiment = classification.get("sentiment", "neutral")
        confidence = classification.get("confidence", 0)
        key_issues = classification.get("key_issues", [])
        
        # Check for critical issues
        critical_keywords = ["palsu", "scam", "tipu", "bahaya", "iritasi"]
        has_critical = any(
            keyword in " ".join(key_issues).lower() 
            for keyword in critical_keywords
        )
        
        # Determine alert level
        if has_critical or (sentiment == "negative" and confidence > 95):
            level = AlertLevel.CRITICAL
        elif sentiment == "negative" and confidence > 85:
            level = AlertLevel.HIGH
        elif sentiment == "negative" and confidence > 70:
            level = AlertLevel.MEDIUM
        elif sentiment == "mixed":
            level = AlertLevel.LOW
        else:
            return None
        
        return {
            "review_id": classification.get("id"),
            "level": level.value,
            "sentiment": sentiment,
            "confidence": confidence,
            "issues": key_issues,
            "action_needed": classification.get("recommended_action", ""),
            "created_at": datetime.now().isoformat()
        }
    
    def _calculate_stats(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate review statistics."""
        total = len(classifications)
        if total == 0:
            return {}
        
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        confidence_sum = 0
        
        for c in classifications:
            sentiment = c.get("sentiment", "neutral")
            if sentiment in sentiment_counts:
                sentiment_counts[sentiment] += 1
            confidence_sum += c.get("confidence", 0)
        
        return {
            "total": total,
            "sentiment_distribution": sentiment_counts,
            "average_confidence": round(confidence_sum / total, 2),
            "positive_rate": round(sentiment_counts["positive"] / total * 100, 2),
            "negative_rate": round(sentiment_counts["negative"] / total * 100, 2)
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for review management dashboard."""
        if not self._reviews_cache:
            return {
                "reviews": [],
                "stats": {},
                "alerts": [],
                "message": "No reviews analyzed yet"
            }
        
        stats = self._calculate_stats(self._reviews_cache)
        alerts = [self._check_alert(r) for r in self._reviews_cache]
        alerts = [a for a in alerts if a is not None]
        
        return {
            "reviews": self._reviews_cache,
            "stats": stats,
            "alerts": alerts,
            "last_updated": datetime.now().isoformat()
        }
    
    def export_report(self, format: str = "json") -> str:
        """Export review analysis report."""
        dashboard_data = self.get_dashboard_data()
        
        if format == "json":
            return json.dumps(dashboard_data, indent=2, ensure_ascii=False)
        elif format == "text":
            return self._format_text_report(dashboard_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _format_text_report(self, data: Dict[str, Any]) -> str:
        """Format report as text."""
        stats = data.get("stats", {})
        reviews = data.get("reviews", [])
        alerts = data.get("alerts", [])
        
        lines = [
            "=" * 60,
            "RANKUP AI - REVIEW ANALYSIS REPORT",
            "=" * 60,
            f"Total Reviews: {stats.get('total', 0)}",
            f"Positive Rate: {stats.get('positive_rate', 0)}%",
            f"Negative Rate: {stats.get('negative_rate', 0)}%",
            f"Average Confidence: {stats.get('average_confidence', 0)}%",
            "",
            "-" * 60,
            "SENTIMENT DISTRIBUTION:",
        ]
        
        for sent, count in stats.get("sentiment_distribution", {}).items():
            lines.append(f"  {sent.capitalize()}: {count}")
        
        if alerts:
            lines.extend([
                "",
                "-" * 60,
                f"ALERTS ({len(alerts)} critical reviews):",
            ])
            for alert in alerts[:5]:  # Show top 5
                lines.append(f"  [{alert['level'].upper()}] Review #{alert['review_id']}")
                lines.append(f"    Issues: {', '.join(alert.get('issues', []))}")
                lines.append(f"    Action: {alert.get('action_needed', 'None')}")
        
        lines.extend([
            "",
            "=" * 60,
            "TOP 5 REVIEWS:",
            "-" * 60,
        ])
        
        for review in reviews[:5]:
            lines.append(f"#{review.get('id')}: {review.get('text', '')[:80]}...")
            lines.append(f"  Sentiment: {review.get('sentiment', 'N/A')} ({review.get('confidence', 0)}%)")
            lines.append(f"  Reply: {review.get('reply_text', 'N/A')}")
            lines.append("")
        
        return "\n".join(lines)
