#!/usr/bin/env python3
"""
RankUp AI - LLM Response Diagnostic
====================================
Debug empty responses and optimization issues.
"""

import sys
import os
import json

sys.path.insert(0, '/home/ubuntu/rankup-ai')

from openai import OpenAI
from scraper.config import config

def debug_reply_drafter():
    """Debug reply drafter empty responses"""
    print("\n🔍 DEBUGGING REPLY DRAFTER")
    print("="*60)
    
    client = OpenAI(
        api_key=config.llm.api_key,
        base_url=config.llm.base_url,
        timeout=config.llm.timeout,
    )
    
    # Simplified prompt
    system_prompt = """Kamu adalah customer service TikTok Shop. Draft reply SINGKAT (50-100 karakter) untuk review.

Review: "Barang sampe pecah:("
Sentiment: negative

Return JSON:
{"reply_text": "teks reply", "tone": "empathetic", "follow_up_needed": true}

CONTOH: "Maaf banget kak 🙏 Segera DM admin, kami ganti gratis!"
"""
    
    print("\n📤 Test 1: Simple prompt")
    try:
        response = client.chat.completions.create(
            model=config.llm.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Draft reply"},
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        
        raw = response.choices[0].message.content
        print(f"Response: '{raw}'")
        print(f"Length: {len(raw) if raw else 0}")
        
        if raw:
            parsed = json.loads(raw)
            print(f"Parsed: {parsed}")
        else:
            print("❌ EMPTY RESPONSE!")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Test without json_object format
    print("\n📤 Test 2: Without json_object format")
    try:
        response = client.chat.completions.create(
            model=config.llm.model,
            messages=[
                {"role": "system", "content": "Reply to negative review in 50-100 chars Indonesian. Be empathetic."},
                {"role": "user", "content": "Review: 'Barang sampe pecah:('"},
            ],
            temperature=0.3,
            max_tokens=150,
        )
        
        raw = response.choices[0].message.content
        print(f"Response: '{raw}'")
        print(f"Length: {len(raw) if raw else 0}")
            
    except Exception as e:
        print(f"Error: {e}")

def debug_listing_optimizer():
    """Debug listing optimizer returning original"""
    print("\n\n🔍 DEBUGGING LISTING OPTIMIZER")
    print("="*60)
    
    client = OpenAI(
        api_key=config.llm.api_key,
        base_url=config.llm.base_url,
        timeout=config.llm.timeout,
    )
    
    # Force explicit instruction
    system_prompt = """IMPORTANT: You MUST rewrite and improve the listing. Do NOT copy the original.

Create a NEW, BETTER version with:
- Catchier title with emojis
- Persuasive description with urgency
- Social proof elements

Return JSON with optimized_title and optimized_description that are DIFFERENT from original."""
    
    user_prompt = f"""OPTIMIZE THIS LISTING:

Original Title: Serum Vitamin C Whitening Ampoule 30ml
Original Description: Serum vitamin C untuk mencerahkan kulit. Cocok untuk semua jenis kulit. Gunakan 2x sehari.

CREATE NEW VERSION:"""
    
    print("\n📤 Sending optimization request...")
    try:
        response = client.chat.completions.create(
            model=config.llm.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,  # Higher creativity
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        
        raw = response.choices[0].message.content
        print(f"\n📥 Raw Response:\n{raw}")
        
        if raw:
            parsed = json.loads(raw)
            print(f"\n📊 Parsed:")
            print(json.dumps(parsed, indent=2, ensure_ascii=False))
            
            # Check if it's different from original
            if parsed.get('optimized_title') == "Serum Vitamin C Whitening Ampoule 30ml":
                print("\n⚠️  WARNING: Title is same as original!")
            else:
                print("\n✅ Title successfully optimized!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_reply_drafter()
    debug_listing_optimizer()
