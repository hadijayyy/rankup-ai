"""
RankUp AI - Minimal Vercel API
===============================

Minimal Flask app for Vercel deployment.
Keyword-based sentiment analysis + reply generation.
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Simple in-memory cache
reviews_cache = []
alerts_cache = []

app = Flask(__name__, static_folder='../dashboard/static', static_url_path='/static')
CORS(app)

# ─── Keywords ───
NEGATIVE_KEYWORDS = [
    'rusak', 'pecah', 'palsu', 'tipu', 'jelek', 'buruk', 'kecewa',
    'gak cocok', 'tidak sesuai', 'parah', 'hancur', 'cacat', 'minus',
    'ga sesuai', 'barang datang', 'error', 'bermasalah', 'retur',
    'refund', 'komplain', 'nggak bagus', 'gak bagus', 'tidak bagus',
    'lambat', 'lama', 'jelek banget', 'parah banget', 'tolol', 'bangsat',
    'anjing', 'goblok', 'kontol', 'memek', 'tai', 'sialan', 'brengsek',
    'penipuan', 'scam', 'bohong', 'pura-pura', 'tipu-tipu',
    'sakit', 'gatal', 'iritasi', 'alergi', 'bahaya'
]

POSITIVE_KEYWORDS = [
    'bagus', 'mantap', 'suka', 'puas', 'oke', 'baik', 'keren',
    'top', 'worth it', 'rekomendasi', 'recommended', 'best', 'love',
    'cocok', 'sesuai', 'cepat', 'ramah', 'berkualitas', 'original',
    'berfungsi', 'memuaskan', 'excellent', 'perfect', 'great',
    'good', 'nice', 'amazing', 'awesome', 'terbaik', 'satisfy',
    'berhasil', 'berkhasiat', 'manjur', 'tokcer', 'joss', 'joss banget',
    'puas banget', 'suka banget', 'mantul', 'kece', 'stylish', 'elegan',
    'pasti repurchase', 'beli lagi', 'repeat order'
]


def analyze_sentiment(text):
    """Classify sentiment based on keywords."""
    text_lower = text.lower()
    
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    
    # Check for ALL CAPS (anger signal)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    caps_bonus = 1 if caps_ratio > 0.6 and len(text) > 5 else 0
    
    # Check for exclamation marks (intensity)
    excl_count = text.count('!') + text.count('!!') + text.count('!!!')
    
    if neg_count > pos_count:
        confidence = min(98, 70 + neg_count * 10 + caps_bonus * 5)
        if excl_count >= 2:
            confidence = min(98, confidence + 5)
        return 'negative', confidence, neg_count
    elif pos_count > neg_count:
        confidence = min(98, 75 + pos_count * 8)
        return 'positive', confidence, pos_count
    else:
        # Neutral with tie-breaking from caps/excl
        if caps_bonus or excl_count >= 2:
            return 'negative', 75, 0
        return 'neutral', 80, 0


def generate_reply(sentiment, review_text):
    """Generate contextual reply based on sentiment."""
    text_lower = review_text.lower()
    
    if sentiment == 'negative':
        if any(kw in text_lower for kw in ['pecah', 'hancur', 'rusak', 'cacat']):
            return 'Mohon maaf ya kak 🙏 Barang pecah/rusak bisa langsung DM admin untuk penggantian. Kami tanggung jawab penuh! 💪'
        elif any(kw in text_lower for kw in ['palsu', 'tipu', 'scam', 'penipuan']):
            return 'Kami jamin produk 100% original kak! 🙏 Jika ragu, bisa cek sertifikat di DM admin. Kami siap bantu! 😊'
        elif any(kw in text_lower for kw in ['lambat', 'lama']):
            return 'Maaf ya kak pengirimannya lambat 🙏 Kami bantu cek resinya. DM admin ya kak! 📦'
        elif any(kw in text_lower for kw in ['sakit', 'gatal', 'iritasi']):
            return 'Mohon maaf kak 🙏 Untuk keamanan, hentikan pemakaian dulu ya. DM admin untuk konsultasi lebih lanjut! 💚'
        else:
            return 'Maaf ya kak 🙏 Kami bantu selesaikan masalahnya. Silakan DM admin dengan nomor order ya! Kami pastikan puas 😊'
    elif sentiment == 'positive':
        if any(kw in text_lower for kw in ['repurchase', 'beli lagi', 'repeat']):
            return 'Makasih banget kak! 🫶 Seneng kamu mau repeat order! Jangan lupa claim voucher loyalitas di chat ya! 🎁'
        else:
            return 'Makasih banyak kak! 🫶 Seneng kamu suka produknya! Jangan lupa cek produk baru kami ya! ⭐'
    else:
        return 'Makasih reviewnya kak! 🙏 Feedback kamu sangat berharga untuk kami. Semoga bermanfaat ya! 😊'


def detect_key_issues(text):
    """Extract key issues from negative review."""
    text_lower = text.lower()
    issues = []
    
    if any(kw in text_lower for kw in ['pecah', 'hancur', 'rusak', 'cacat']):
        issues.append('Kondisi barang rusak/pecah')
    if any(kw in text_lower for kw in ['palsu', 'tipu', 'scam', 'penipuan']):
        issues.append('Keaslian produk dipertanyakan')
    if any(kw in text_lower for kw in ['lambat', 'lama']):
        issues.append('Pengiriman lambat')
    if any(kw in text_lower for kw in ['beda', 'tidak sesuai', 'gak cocok', 'ga sesuai']):
        issues.append('Tidak sesuai deskripsi')
    if any(kw in text_lower for kw in ['sakit', 'gatal', 'iritasi', 'alergi']):
        issues.append('Efek samping/kesehatan')
    if any(kw in text_lower for kw in ['kecil', 'tipis', 'abang']):
        issues.append('Ukuran/kualitas di bawah ekspektasi')
    if any(kw in text_lower for kw in ['bau', 'amis', 'apes']):
        issues.append('Bau tidak enak')
    if any(kw in text_lower for kw in ['jelek', 'buruk', 'parah']):
        issues.append('Kualitas produk buruk')
    if any(kw in text_lower for kw in ['kecewa', 'menyesal']):
        issues.append('Customer kecewa')
    if not issues:
        issues.append('Umum')
    
    return issues


# ─── Routes ───

@app.route('/')
def index():
    """Serve main dashboard."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/classify', methods=['POST'])
def classify_review():
    """Classify a single review."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON body provided"}), 400
        
        review = data.get('review', '').strip()
        if not review:
            return jsonify({"error": "No review provided"}), 400
        
        sentiment, confidence, match_count = analyze_sentiment(review)
        
        if sentiment == 'negative':
            key_issues = detect_key_issues(review)
            action = 'Hubungi customer untuk resolve masalah'
        elif sentiment == 'positive':
            key_issues = ['Customer puas']
            action = 'Ajukan repurchase atau bundle'
        else:
            key_issues = ['Netral']
            action = 'Monitor review lanjutan'
        
        reply = generate_reply(sentiment, review)
        
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
        
        # Auto-alert for critical reviews
        if sentiment == 'negative' and confidence >= 85:
            alert = {
                "review_id": len(reviews_cache),
                "level": "critical" if confidence >= 90 else "high",
                "text": review[:100],
                "issues": key_issues
            }
            alerts_cache.append(alert)
        
        # Keep only last 200 reviews
        if len(reviews_cache) > 200:
            reviews_cache.pop(0)
        if len(alerts_cache) > 50:
            alerts_cache.pop(0)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/classify-bulk', methods=['POST'])
def classify_bulk():
    """Classify multiple reviews."""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON body provided"}), 400
        
        reviews = data.get('reviews', [])
        if not reviews or not isinstance(reviews, list):
            return jsonify({"error": "Provide reviews as an array"}), 400
        
        results = []
        new_alerts = []
        
        for i, review in enumerate(reviews):
            review = str(review).strip()
            if not review:
                continue
            
            sentiment, confidence, match_count = analyze_sentiment(review)
            
            if sentiment == 'negative':
                key_issues = detect_key_issues(review)
                action = 'Hubungi customer untuk resolve masalah'
            elif sentiment == 'positive':
                key_issues = ['Customer puas']
                action = 'Ajukan repurchase atau bundle'
            else:
                key_issues = ['Netral']
                action = 'Monitor review lanjutan'
            
            reply = generate_reply(sentiment, review)
            
            result = {
                "id": len(reviews_cache) + i + 1,
                "review": review,
                "sentiment": sentiment,
                "confidence": confidence,
                "key_issues": key_issues,
                "recommended_action": action,
                "reply_text": reply,
                "reply_tone": "empathetic"
            }
            
            results.append(result)
            reviews_cache.append(result)
            
            if sentiment == 'negative' and confidence >= 85:
                alert = {
                    "review_id": len(reviews_cache),
                    "level": "critical" if confidence >= 90 else "high",
                    "text": review[:100],
                    "issues": key_issues
                }
                new_alerts.append(alert)
                alerts_cache.append(alert)
        
        total = len(results)
        positive = sum(1 for r in results if r['sentiment'] == 'positive')
        negative = sum(1 for r in results if r['sentiment'] == 'negative')
        neutral = sum(1 for r in results if r['sentiment'] == 'neutral')
        
        stats = {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_rate": round(positive / total * 100, 1) if total > 0 else 0,
            "negative_rate": round(negative / total * 100, 1) if total > 0 else 0,
            "average_confidence": round(sum(r['confidence'] for r in results) / total, 1) if total > 0 else 0
        }
        
        # Keep cache bounded
        if len(reviews_cache) > 200:
            reviews_cache[:] = reviews_cache[-200:]
        if len(alerts_cache) > 50:
            alerts_cache[:] = alerts_cache[-50:]
        
        return jsonify({
            "reviews": results,
            "stats": stats,
            "alerts": new_alerts,
            "total_reviews": total
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reviews')
def get_reviews():
    """Get cached reviews."""
    return jsonify({
        "total": len(reviews_cache),
        "reviews": reviews_cache[-50:]  # Last 50
    })


@app.route('/api/alerts')
def get_alerts():
    """Get active alerts."""
    return jsonify({
        "total": len(alerts_cache),
        "alerts": alerts_cache[-20:]  # Last 20
    })


@app.route('/api/stats')
def get_stats():
    """Get overall statistics."""
    total = len(reviews_cache)
    if total == 0:
        return jsonify({
            "total_reviews": 0,
            "total": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "positive_rate": 0,
            "negative_rate": 0,
            "alerts": 0
        })
    
    positive = sum(1 for r in reviews_cache if r.get('sentiment') == 'positive')
    negative = sum(1 for r in reviews_cache if r.get('sentiment') == 'negative')
    neutral = sum(1 for r in reviews_cache if r.get('sentiment') == 'neutral')
    
    return jsonify({
        "total_reviews": total,
        "total": total,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "positive_rate": round(positive / total * 100, 1),
        "negative_rate": round(negative / total * 100, 1),
        "alerts": len(alerts_cache)
    })


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "version": "1.0.0",
        "reviews_cached": len(reviews_cache),
        "alerts_cached": len(alerts_cache)
    })


if __name__ == '__main__':
    app.run(debug=True, port=8000)
