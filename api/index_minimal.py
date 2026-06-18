"""
RankUp AI - Minimal Vercel API
===============================

Minimal Flask app for Vercel deployment.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Simple in-memory cache
reviews_cache = []

app = Flask(__name__, static_folder='../dashboard/static', static_url_path='/static')
CORS(app)


@app.route('/')
def index():
    """Serve main dashboard."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/classify', methods=['POST'])
def classify_review():
    """Classify a single review (simplified version)."""
    try:
        data = request.json
        review = data.get('review', '')
        
        if not review:
            return jsonify({"error": "No review provided"}), 400
        
        # Simple sentiment analysis based on keywords
        review_lower = review.lower()
        
        # Negative keywords
        negative_keywords = ['rusak', 'pecah', 'palsu', 'tipu', 'jelek', 'buruk', 'kecewa', 'gak cocok', 'tidak sesuai']
        positive_keywords = ['bagus', 'mantap', 'suka', 'puas', 'oke', 'baik', 'keren', 'top', 'worth it', 'rekomendasi']
        
        # Count matches
        negative_count = sum(1 for word in negative_keywords if word in review_lower)
        positive_count = sum(1 for word in positive_keywords if word in review_lower)
        
        # Determine sentiment
        if negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(95, 70 + negative_count * 10)
            key_issues = ['Barang tidak sesuai ekspektasi']
            action = 'Hubungi customer untuk resolve masalah'
        elif positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(98, 75 + positive_count * 10)
            key_issues = ['Customer puas']
            action = 'Ajukan repurchase atau bundle'
        else:
            sentiment = 'neutral'
            confidence = 85
            key_issues = ['Netral']
            action = 'Monitor review lanjutan'
        
        # Generate simple reply
        if sentiment == 'negative':
            reply = 'Maaf ya kak 🙏 Kami bantu selesaikan. DM admin ya! 😊'
        elif sentiment == 'positive':
            reply = 'Makasih kak! Seneng kamu suka! 🫶 Jangan lupa repurchase ya!'
        else:
            reply = 'Makasih reviewnya kak! 🙏 Semoga bermanfaat ya!'
        
        # Store in cache
        result = {
            "review": review,
            "sentiment": sentiment,
            "confidence": confidence,
            "key_issues": key_issues,
            "recommended_action": action,
            "reply_text": reply,
            "reply_tone": "empathetic"
        }
        
        reviews_cache.append(result)
        
        # Keep only last 100 reviews
        if len(reviews_cache) > 100:
            reviews_cache.pop(0)
        
        return jsonify(result)
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
        
        results = []
        alerts = []
        
        for i, review in enumerate(reviews):
            # Simple sentiment analysis
            review_lower = review.lower()
            
            negative_keywords = ['rusak', 'pecah', 'palsu', 'tipu', 'jelek', 'buruk', 'kecewa']
            positive_keywords = ['bagus', 'mantap', 'suka', 'puas', 'oke', 'baik', 'keren']
            
            negative_count = sum(1 for word in negative_keywords if word in review_lower)
            positive_count = sum(1 for word in positive_keywords if word in review_lower)
            
            if negative_count > positive_count:
                sentiment = 'negative'
                confidence = min(95, 70 + negative_count * 10)
                key_issues = ['Barang tidak sesuai ekspektasi']
                action = 'Hubungi customer'
                reply = 'Maaf ya kak 🙏 Kami bantu selesaikan. DM admin ya!'
            elif positive_count > negative_count:
                sentiment = 'positive'
                confidence = min(98, 75 + positive_count * 10)
                key_issues = ['Customer puas']
                action = 'Ajukan repurchase'
                reply = 'Makasih kak! Seneng kamu suka! 🫶'
            else:
                sentiment = 'neutral'
                confidence = 85
                key_issues = ['Netral']
                action = 'Monitor'
                reply = 'Makasih reviewnya kak! 🙏'
            
            result = {
                "id": i + 1,
                "text": review,
                "sentiment": sentiment,
                "confidence": confidence,
                "key_issues": key_issues,
                "recommended_action": action,
                "reply_text": reply
            }
            
            results.append(result)
            
            # Check for alerts
            if sentiment == 'negative' and confidence > 85:
                alerts.append({
                    "review_id": i + 1,
                    "level": "high",
                    "issues": key_issues
                })
        
        # Calculate stats
        total = len(results)
        positive = sum(1 for r in results if r['sentiment'] == 'positive')
        negative = sum(1 for r in results if r['sentiment'] == 'negative')
        
        stats = {
            "total": total,
            "positive_rate": round(positive / total * 100, 2) if total > 0 else 0,
            "negative_rate": round(negative / total * 100, 2) if total > 0 else 0,
            "average_confidence": round(sum(r['confidence'] for r in results) / total, 2) if total > 0 else 0
        }
        
        return jsonify({
            "reviews": results,
            "stats": stats,
            "alerts": alerts,
            "total_reviews": total
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reviews')
def get_reviews():
    """Get cached reviews."""
    return jsonify({
        "total": len(reviews_cache),
        "reviews": reviews_cache
    })


@app.route('/api/stats')
def get_stats():
    """Get statistics."""
    total = len(reviews_cache)
    if total == 0:
        return jsonify({"total": 0})
    
    positive = sum(1 for r in reviews_cache if r.get('sentiment') == 'positive')
    negative = sum(1 for r in reviews_cache if r.get('sentiment') == 'negative')
    
    return jsonify({
        "total": total,
        "positive": positive,
        "negative": negative,
        "positive_rate": round(positive / total * 100, 2),
        "negative_rate": round(negative / total * 100, 2)
    })


if __name__ == '__main__':
    app.run(debug=True, port=8000)
