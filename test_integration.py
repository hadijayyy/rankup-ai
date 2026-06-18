#!/usr/bin/env python3
"""
RankUp AI - Integration Test
==============================
Tests all 4 LLM-dependent features with DeepSeek V4 Flash via OpenCode-Go.
"""

import sys
import os
import json

# Add the rankup-ai directory to path
sys.path.insert(0, '/home/ubuntu/rankup-ai')

from ai_engine import ListingAnalyzer, ListingOptimizer, ReviewClassifier, ReplyDrafter

def test_listing_analyzer():
    """Test 1: Analyze Listing"""
    print("\n" + "="*60)
    print("TEST 1: LISTING ANALYZER")
    print("="*60)
    
    analyzer = ListingAnalyzer()
    
    product_data = {
        "title": "Serum Vitamin C Whitening Ampoule 30ml",
        "description": "Serum vitamin C untuk mencerahkan kulit. Cocok untuk semua jenis kulit. Gunakan 2x sehari.",
        "price": "Rp 89.000",
        "rating": 4.5,
        "sales_count": 1250,
        "review_count": 89,
        "hashtags": ["serumvco", "whitening", "skincare"],
        "images": ["img1.jpg", "img2.jpg"]
    }
    
    try:
        result = analyzer.analyze_listing(product_data)
        print(f"✅ Score: {result['score']}/10")
        print(f"📊 Weaknesses: {len(result['weaknesses'])} found")
        print(f"💪 Strengths: {len(result['strengths'])} found")
        print(f"🎯 Recommendations: {len(result['recommendations'])} found")
        print(f"\nTop Recommendation:")
        if result['recommendations']:
            print(f"  - {result['recommendations'][0]}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_listing_optimizer():
    """Test 2: Optimize Listing"""
    print("\n" + "="*60)
    print("TEST 2: LISTING OPTIMIZER")
    print("="*60)
    
    optimizer = ListingOptimizer()
    
    product_data = {
        "title": "Serum Vitamin C Whitening Ampoule 30ml",
        "description": "Serum vitamin C untuk mencerahkan kulit. Cocok untuk semua jenis kulit. Gunakan 2x sehari.",
        "price": "Rp 89.000",
        "rating": 4.5,
        "sales_count": 1250,
        "review_count": 89,
        "hashtags": ["serumvco", "whitening", "skincare"]
    }
    
    try:
        result = optimizer.optimize_listing(product_data)
        print(f"✅ New Title ({len(result['optimized_title'])} char):")
        print(f"   {result['optimized_title']}")
        print(f"\n📝 New Description ({len(result['optimized_description'])} char):")
        print(f"   {result['optimized_description'][:100]}...")
        
        if 'bullet_points' in result:
            print(f"\n📋 Bullet Points ({len(result['bullet_points'])} items):")
            for bp in result['bullet_points']:
                print(f"   • {bp}")
        
        print(f"\n🔄 Changes Made: {len(result['changes_made'])}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_review_classifier():
    """Test 3: Classify Reviews"""
    print("\n" + "="*60)
    print("TEST 3: REVIEW CLASSIFIER")
    print("="*60)
    
    classifier = ReviewClassifier()
    
    reviews = [
        "Ga cocok sama kulitku:( padahal udah coba 2 minggu",
        "MANTAAAAP BANGET!!! Worth it banget pokoknya🔥🔥🔥",
        "Yaudah lah ya, biasa aja gitu... ga ada efek apa-apa",
        "Pengiriman cepat, packaging ok, tapi belum tau hasilnya gimana",
        "BARANG PALSU!! Jangan beli disini!!!*!*!*!"
    ]
    
    try:
        results = classifier.classify_reviews_batch(reviews)
        
        print(f"✅ Classified {len(results)} reviews:\n")
        
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        
        for i, (review, result) in enumerate(zip(reviews, results), 1):
            sentiment = result['sentiment']
            confidence = result['confidence']
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            print(f"{i}. {review[:40]}...")
            print(f"   Sentiment: {sentiment.upper()} ({confidence}% confidence)")
            if result.get('key_issues'):
                print(f"   Issues: {result['key_issues'][0]}")
            print()
        
        print(f"📊 Sentiment Distribution:")
        for sent, count in sentiment_counts.items():
            print(f"   {sent}: {count}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_reply_drafter():
    """Test 4: Draft Replies"""
    print("\n" + "="*60)
    print("TEST 4: REPLY DRAFTER")
    print("="*60)
    
    drafter = ReplyDrafter()
    
    reviews = [
        {"text": "Barang sampe pecah:(", "rating": 1, "sentiment": "negative"},
        {"text": "Best serum ever! Kulit jadi glowing banget✨ rekomendasi banget!", "rating": 5, "sentiment": "positive"},
        {"text": "Produk oke sih, tapi pengiriman lama banget 5 hari baru sampe", "rating": 3, "sentiment": "mixed"}
    ]
    
    product_info = {
        "title": "Serum Vitamin C Whitening Ampoule 30ml",
        "price": "Rp 89.000"
    }
    
    try:
        results = []
        for review in reviews:
            result = drafter.draft_reply(review, product_info=product_info)
            results.append(result)
        
        print(f"✅ Drafted {len(results)} replies:\n")
        
        for i, (review, result) in enumerate(zip(reviews, results), 1):
            print(f"{i}. Review: \"{review['text'][:40]}...\"")
            print(f"   Reply ({len(result['reply_text'])} char): {result['reply_text']}")
            print(f"   Tone: {result['tone']}")
            if 'star_rating_suggestion' in result:
                print(f"   Suggested Rating: {'⭐' * result['star_rating_suggestion']}")
            print()
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("\n🚀 RANKUP AI - INTEGRATION TEST")
    print("="*60)
    print("Testing all 4 LLM features with DeepSeek V4 Flash via OpenCode-Go")
    print("="*60)
    
    tests = [
        ("Listing Analyzer", test_listing_analyzer),
        ("Listing Optimizer", test_listing_optimizer),
        ("Review Classifier", test_review_classifier),
        ("Reply Drafter", test_reply_drafter),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n🎯 Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! DeepSeek V4 Flash integration is working!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
