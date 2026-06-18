"""
RankUp AI - Vercel Serverless API Entry Point
==============================================

Flask app adapted for Vercel serverless deployment.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import ReviewClassifier, ReplyDrafter, BulkReviewManager

app = Flask(__name__, static_folder='../dashboard/static', static_url_path='/static')
CORS(app)

# Initialize AI engines
classifier = ReviewClassifier()
drafter = ReplyDrafter()
manager = BulkReviewManager()


@app.route('/')
def index():
    """Serve main dashboard."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/classify', methods=['POST'])
def classify_review():
    """Classify a single review."""
    try:
        data = request.json
        review = data.get('review', '')
        
        if not review:
            return jsonify({"error": "No review provided"}), 400
        
        # Classify review
        result = classifier.classify_review(review)
        
        # Generate reply
        review_data = {
            "text": review,
            "rating": 3,
            "sentiment": result.get('sentiment', 'neutral')
        }
        reply_result = drafter.draft_reply(review_data)
        
        # Combine results
        combined = {
            "review": review,
            "sentiment": result.get('sentiment'),
            "confidence": result.get('confidence'),
            "key_issues": result.get('key_issues', []),
            "recommended_action": result.get('recommended_action'),
            "reply_text": reply_result.get('reply_text'),
            "reply_tone": reply_result.get('tone')
        }
        
        return jsonify(combined)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/classify-bulk', methods=['POST'])
def classify_bulk():
    """Classify multiple reviews."""
    try:
        data = request.json
        reviews = data.get('reviews', [])
        
        if not reviews:
            return jsonify({"error": "No reviews provided"}), 400
        
        # Process bulk reviews
        result = manager.classify_bulk_reviews(reviews)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reviews')
def get_reviews():
    """Get cached reviews."""
    try:
        dashboard_data = manager.get_dashboard_data()
        return jsonify(dashboard_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts')
def get_alerts():
    """Get alerts."""
    try:
        dashboard_data = manager.get_dashboard_data()
        alerts = dashboard_data.get('alerts', [])
        return jsonify({
            "total": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Get statistics."""
    try:
        dashboard_data = manager.get_dashboard_data()
        stats = dashboard_data.get('stats', {})
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# For local development
if __name__ == '__main__':
    app.run(debug=True, port=8000)
