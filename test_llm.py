#!/usr/bin/env python3
"""
RankUp AI — LIVE LLM TEST
===========================
Tests all 5 LLM-powered stages with real API calls.
Uses OpenRouter (DeepSeek V4 Flash).
"""

import sys
import os
import json
from openai import OpenAI

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─── LLM CLIENT ──────────────────────────────────────────────────────────

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
MODEL = "deepseek/deepseek-chat-v3-0324"

def call_llm(system_prompt, user_prompt):
    """Call LLM and return response text."""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return resp.choices[0].message.content


# ─── SAMPLE DATA ─────────────────────────────────────────────────────────

PRODUCT = {
    "name": "Serum Vitamin C Brightening 30ml",
    "price": "Rp 89.000",
    "original_price": "Rp 150.000",
    "discount": "40%",
    "sales_count": 1250,
    "rating": 4.6,
    "review_count": 342,
    "description": "Serum vitamin c untuk wajah. Bagus buat kulit kusam. Bisa bikin wajah cerah. Cocok untuk semua jenis kulit. Aman dipakai sehari-hari.",
    "hashtags": ["#serumvC", "#vitaminc", "#skincare", "#brightening", "#wajahcerah"],
}

REVIEWS = [
    {"reviewer": "Rina S.", "rating": 5, "text": "Bagus banget! Wajah jadi cerah setelah 2 minggu pakai. Repurchase!"},
    {"reviewer": "Maya P.", "rating": 5, "text": "Cocok di kulit aku yang sensitif. Ga bikin iritasi. Love it!"},
    {"reviewer": "Dewi K.", "rating": 4, "text": "Lumayan sih, tapi agak lengket pas awal apply. Tapi setelah meresap oke."},
    {"reviewer": "Sari A.", "rating": 2, "text": "Kok ga cocok ya? Muka jadi bruntusan. Padahal udah sesuai type kulit."},
    {"reviewer": "Bunga R.", "rating": 1, "text": "Pengiriman lama, packaging rusak. Produk belum dicoba tapi udah kecewa."},
    {"reviewer": "Anisa T.", "rating": 5, "text": "Best serum VCI di harga segini! Hasil keliatan di minggu ke-2."},
    {"reviewer": "Putri M.", "rating": 3, "text": "Biasa aja sih, ga se-mujizat yang dikata orang. Mungkin butuh waktu lebih lama."},
    {"reviewer": "Ratna D.", "rating": 5, "text": "Beli buat ibu, ibu suka banget! Katanya kulit jadi kenyal. Thanks seller!"},
    {"reviewer": "Lestari N.", "rating": 2, "text": "Beli 2 dapat 1 ga sesuai gambar. Beda banget dari yang di iklan."},
    {"reviewer": "Fitri H.", "rating": 4, "text": "Oke lah untuk harga segini. Ga expect terlalu banyak. Yang pasti aman."},
]


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_stage(num, title):
    print(f"\n{'─'*60}")
    print(f"  STAGE {num}: {title}")
    print(f"{'─'*60}\n")


# ═════════════════════════════════════════════════════════════════════════
# STAGE 2: AI LISTING ANALYSIS (REAL LLM)
# ═════════════════════════════════════════════════════════════════════════

def stage_analyze():
    print_stage(2, "AI LISTING ANALYSIS (REAL LLM)")
    
    system = """You are an expert TikTok Shop listing analyst. 
Analyze the product listing and return a JSON object with:
- score: integer 1-10 (listing quality)
- strengths: list of strings (what's good)
- weaknesses: list of strings (what needs improvement)
- recommendations: list of strings (specific actionable fixes)

Be specific and actionable. Return ONLY valid JSON, no other text."""

    user = f"""Analyze this TikTok Shop listing:

Product: {PRODUCT['name']}
Price: {PRODUCT['price']} (was {PRODUCT['original_price']}, {PRODUCT['discount']} off)
Sales: {PRODUCT['sales_count']}
Rating: {PRODUCT['rating']}/5 ({PRODUCT['review_count']} reviews)
Description: {PRODUCT['description']}
Hashtags: {', '.join(PRODUCT['hashtags'])}

Return JSON analysis."""
    
    print("🧠 Calling LLM for analysis...")
    result = call_llm(system, user)
    
    # Parse JSON
    try:
        # Try to extract JSON from response
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        analysis = json.loads(result.strip())
    except:
        print("⚠️  JSON parse failed, using raw output")
        analysis = {"raw": result}
    
    print(f"\n📊 RESULT:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    return analysis


# ═════════════════════════════════════════════════════════════════════════
# STAGE 3: AI LISTING OPTIMIZATION (REAL LLM)
# ═════════════════════════════════════════════════════════════════════════

def stage_optimize():
    print_stage(3, "AI LISTING OPTIMIZATION (REAL LLM)")
    
    system = """You are an expert TikTok Shop listing optimizer.
Create an optimized version of the listing.
Return a JSON object with:
- optimized_title: string (max 80 chars, catchy, with emoji)
- optimized_description: string (detailed, with benefits, ingredients, how-to, social proof, CTA)
- optimized_hashtags: list of 10 relevant trending hashtags
- changes_made: list of strings (what you changed and why)
- expected_impact: string (predicted improvement)

TikTok style: short, catchy, emoji-friendly, urgency.
Return ONLY valid JSON, no other text."""

    user = f"""Optimize this TikTok Shop listing:

Current Title: {PRODUCT['name']}
Current Description: {PRODUCT['description']}
Current Hashtags: {', '.join(PRODUCT['hashtags'])}
Price: {PRODUCT['price']} ({PRODUCT['discount']} off)
Sales: {PRODUCT['sales_count']}
Rating: {PRODUCT['rating']}/5

Return optimized JSON."""
    
    print("🧠 Calling LLM for optimization...")
    result = call_llm(system, user)
    
    try:
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        optimized = json.loads(result.strip())
    except:
        optimized = {"raw": result}
    
    print(f"\n📊 RESULT:")
    print(json.dumps(optimized, indent=2, ensure_ascii=False))
    return optimized


# ═════════════════════════════════════════════════════════════════════════
# STAGE 4A: AI REVIEW CLASSIFICATION (REAL LLM)
# ═════════════════════════════════════════════════════════════════════════

def stage_classify():
    print_stage(4, "AI REVIEW CLASSIFICATION (REAL LLM)")
    
    reviews_text = "\n".join([
        f"{i+1}. [{r['rating']}⭐] {r['reviewer']}: \"{r['text']}\""
        for i, r in enumerate(REVIEWS)
    ])
    
    system = """You are an expert review analyst for e-commerce.
Classify each review by sentiment and urgency.
Return a JSON object with:
- reviews: list of objects, each with:
  - reviewer: string
  - rating: integer
  - sentiment: "positive" | "negative" | "neutral"
  - urgency: "high" | "medium" | "low"
  - reason: string (brief explanation)
- summary: object with counts (positive, negative, neutral)

Return ONLY valid JSON, no other text."""

    user = f"""Classify these reviews:

{reviews_text}

Return JSON classification."""
    
    print("🧠 Calling LLM for classification...")
    result = call_llm(system, user)
    
    try:
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        classified = json.loads(result.strip())
    except:
        classified = {"raw": result}
    
    print(f"\n📊 RESULT:")
    print(json.dumps(classified, indent=2, ensure_ascii=False))
    return classified


# ═════════════════════════════════════════════════════════════════════════
# STAGE 4B: AI REPLY DRAFTING (REAL LLM)
# ═════════════════════════════════════════════════════════════════════════

def stage_reply():
    print_stage(4, "AI REPLY DRAFTING (REAL LLM)")
    
    # Only reply to negative reviews
    neg_reviews = [r for r in REVIEWS if r["rating"] <= 2]
    reviews_text = "\n".join([
        f"{i+1}. [{r['rating']}⭐] {r['reviewer']}: \"{r['text']}\""
        for i, r in enumerate(neg_reviews)
    ])
    
    system = """You are a professional customer service rep for a TikTok Shop beauty store.
Draft empathetic, professional replies to negative reviews.
Return a JSON object with:
- replies: list of objects, each with:
  - reviewer: string
  - original_review: string
  - rating: integer
  - reply: string (empathetic, solution-oriented, professional)
  - tone: "empathetic" | "professional" | "friendly"
  - follow_up_needed: boolean

Be empathetic, acknowledge the issue, offer solution.
Reply in Bahasa Indonesia.
Return ONLY valid JSON, no other text."""

    user = f"""Draft replies to these negative reviews for "Toko Beauty Official":

{reviews_text}

Product: Serum Vitamin C Brightening 30ml (Rp 89.000)

Return JSON replies."""
    
    print("🧠 Calling LLM for reply drafting...")
    result = call_llm(system, user)
    
    try:
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        replies = json.loads(result.strip())
    except:
        replies = {"raw": result}
    
    print(f"\n📊 RESULT:")
    print(json.dumps(replies, indent=2, ensure_ascii=False))
    return replies


# ═════════════════════════════════════════════════════════════════════════
# STAGE 5: AI WEEKLY REPORT (REAL LLM)
# ═════════════════════════════════════════════════════════════════════════

def stage_report():
    print_stage(5, "AI WEEKLY REPORT (REAL LLM)")
    
    system = """You are a data analyst for an e-commerce optimization service.
Generate a concise weekly intelligence report.
Return a JSON object with:
- summary: string (2-3 sentences overview)
- key_metrics: object (listing_score, reviews_managed, etc.)
- insights: list of 3-5 actionable insights
- action_items: list of 3-5 specific next steps
- report_markdown: string (full formatted report in markdown, max 500 words)

Be concise, data-driven, actionable.
Return ONLY valid JSON, no other text."""

    user = f"""Generate weekly report for:

Client: Toko Beauty Official
Product: {PRODUCT['name']}
Price: {PRODUCT['price']} ({PRODUCT['discount']} off)
Sales: {PRODUCT['sales_count']}
Rating: {PRODUCT['rating']}/5
Reviews: {PRODUCT['review_count']} total
Listing Score: 5/10 (needs optimization)

Competitors:
- VCI Serum Premium ABC: Rp 99.000, 4.7★, 2,100 sales
- Serum VCI Brightening XYZ: Rp 125.000, 4.5★, 890 sales

Reviews this week: 10 (6 positive, 1 neutral, 3 negative)

Return JSON report."""
    
    print("🧠 Calling LLM for report generation...")
    result = call_llm(system, user)
    
    try:
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]
        report = json.loads(result.strip())
    except:
        report = {"raw": result}
    
    print(f"\n📊 RESULT:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


# ═════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════

def main():
    print_header("🚀 RANKUP AI — LIVE LLM TEST")
    print(f"🧠 Model: {MODEL}")
    print(f"🔗 API: OpenRouter")
    print(f"📦 Product: {PRODUCT['name']}")
    print()
    
    results = {}
    
    # Stage 2: Analyze
    results["analyze"] = stage_analyze()
    
    # Stage 3: Optimize
    results["optimize"] = stage_optimize()
    
    # Stage 4A: Classify
    results["classify"] = stage_classify()
    
    # Stage 4B: Reply
    results["reply"] = stage_reply()
    
    # Stage 5: Report
    results["report"] = stage_report()
    
    # Summary
    print_header("✅ LIVE LLM TEST COMPLETE")
    
    stages = [
        ("Analyze", "analyze"),
        ("Optimize", "optimize"),
        ("Classify", "classify"),
        ("Reply", "reply"),
        ("Report", "report"),
    ]
    
    for name, key in stages:
        r = results[key]
        status = "✅" if "raw" not in r else "⚠️"
        print(f"   {status} Stage: {name}")
    
    print()
    print("💰 COST ESTIMATE:")
    print(f"   5 LLM calls × ~$0.01 = ~$0.05 total")
    print()
    print(f"⏰ Finished: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S WIB')}")


if __name__ == "__main__":
    main()
