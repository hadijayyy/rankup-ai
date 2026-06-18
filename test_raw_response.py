#!/usr/bin/env python3
"""
RankUp AI - Detailed LLM Response Test
=======================================
Shows raw LLM responses for debugging.
"""

import sys
import os
import json

sys.path.insert(0, '/home/ubuntu/rankup-ai')

from openai import OpenAI
from scraper.config import config

def test_raw_response():
    """Test raw LLM response"""
    print("\n🔍 TESTING RAW LLM RESPONSE")
    print("="*60)
    
    client = OpenAI(
        api_key=config.llm.api_key,
        base_url=config.llm.base_url,
        timeout=config.llm.timeout,
    )
    
    # Test with listing optimizer prompt
    system_prompt = """Kamu adalah AI optimizer untuk RankUp AI (TikTok Shop listing optimizer).

TUGASAN:
Generate versi optimized dari listing TikTok Shop.

ATURAN WAJIB:
1. **Judul (Title):** Maks 80 karakter, keyword-rich, punchy
2. **Deskripsi:** 150-250 karakter, emotional + benefit-driven
3. **Bullet Points:** 3 fitur utama dengan emoji
4. **Emoji:** Gunakan yang relevan (✨, 💖, 😍, 🧴, 🔥, dll)
5. **Urgency/Scarcity:** "Stok terbatas", "Limited Edition", "Habis dalam X hari"
6. **Social Proof:** Angka penjualan atau testimoni (contoh: "10.000+ terjual")
7. **Call-to-Action:** "Checkout sekarang!", "Buruan sebelum sold out!"
8. **Bahasa Indonesia:** Casual tapi profesional, target market Indonesia female 18-35

Return JSON dengan field:
- "optimized_title": judul baru (string, maks 80 char)
- "optimized_description": deskripsi baru (string, 150-250 char)
- "bullet_points": array 3 string (fitur utama dengan emoji)
- "optimized_hashtags": array 3-5 hashtag strings
- "changes_made": array penjelasan perubahan
- "expected_impact": string dampak yang diharapkan"""
    
    user_prompt = """Please optimize this TikTok Shop product listing:

Title: Serum Vitamin C Whitening Ampoule 30ml
Description: Serum vitamin C untuk mencerahkan kulit. Cocok untuk semua jenis kulit. Gunakan 2x sehari.
Price: Rp 89.000
Rating: 4.5 / 5
Sales count: 1250
Review count: 89
Current hashtags: serumvco, whitening, skincare"""
    
    print("\n📤 SENDING REQUEST...")
    print(f"Model: {config.llm.model}")
    print(f"Base URL: {config.llm.base_url}")
    
    try:
        response = client.chat.completions.create(
            model=config.llm.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        
        raw = response.choices[0].message.content
        print("\n📥 RAW RESPONSE:")
        print(raw)
        
        print("\n" + "="*60)
        print("📊 PARSED RESPONSE:")
        parsed = json.loads(raw)
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
        
        return True
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_raw_response()
