"""
RankUp AI - Simple Web Dashboard
================================

Flask-based dashboard for review management.
"""

from flask import Flask, render_template, request, jsonify
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import ReviewClassifier, ReplyDrafter, BulkReviewManager

app = Flask(__name__)

# Initialize AI engines
classifier = ReviewClassifier()
drafter = ReplyDrafter()
manager = BulkReviewManager()

# In-memory storage (for demo)
reviews_db = []
alerts_db = []


@app.route('/')
def index():
    """Main dashboard page."""
    stats = {
        "total": len(reviews_db),
        "positive": len([r for r in reviews_db if r.get('sentiment') == 'positive']),
        "negative": len([r for r in reviews_db if r.get('sentiment') == 'negative']),
        "neutral": len([r for r in reviews_db if r.get('sentiment') == 'neutral']),
        "alerts": len(alerts_db)
    }
    return render_template('index.html', stats=stats, reviews=reviews_db[:10], alerts=alerts_db[:5])


@app.route('/api/classify', methods=['POST'])
def classify_review():
    """Classify a single review."""
    data = request.json
    review = data.get('review', '')
    
    if not review:
        return jsonify({"error": "No review provided"}), 400
    
    try:
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
        
        # Store in DB
        reviews_db.append(combined)
        
        return jsonify(combined)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/classify-bulk', methods=['POST'])
def classify_bulk():
    """Classify multiple reviews."""
    data = request.json
    reviews = data.get('reviews', [])
    
    if not reviews:
        return jsonify({"error": "No reviews provided"}), 400
    
    try:
        result = manager.classify_bulk_reviews(reviews)
        
        # Store in DB
        reviews_db.extend(result.get('reviews', []))
        alerts_db.extend(result.get('alerts', []))
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reviews')
def get_reviews():
    """Get all reviews."""
    return jsonify({
        "total": len(reviews_db),
        "reviews": reviews_db
    })


@app.route('/api/alerts')
def get_alerts():
    """Get all alerts."""
    return jsonify({
        "total": len(alerts_db),
        "alerts": alerts_db
    })


@app.route('/api/stats')
def get_stats():
    """Get statistics."""
    total = len(reviews_db)
    if total == 0:
        return jsonify({"total": 0})
    
    positive = len([r for r in reviews_db if r.get('sentiment') == 'positive'])
    negative = len([r for r in reviews_db if r.get('sentiment') == 'negative'])
    neutral = len([r for r in reviews_db if r.get('sentiment') == 'neutral'])
    
    return jsonify({
        "total": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "positive_rate": round(positive / total * 100, 2),
        "negative_rate": round(negative / total * 100, 2),
        "alerts": len(alerts_db)
    })


@app.route('/dashboard')
def dashboard():
    """Full dashboard page."""
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
