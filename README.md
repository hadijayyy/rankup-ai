# RankUp AI Review Bot 🤖

**AI-Powered Review Management for TikTok Shop Indonesia**

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DeepSeek V4 Flash](https://img.shields.io/badge/LLM-DeepSeek%20V4%20Flash-green.svg)](https://opencode.ai)
[![Status](https://img.shields.io/badge/status-4%2F4%20tests%20passing-brightgreen.svg)](#testing)

---

## 📖 Apa itu RankUp AI?

**RankUp AI** adalah tool AI untuk manage review TikTok Shop secara otomatis.

**Masalah yang diselesaikan:**
- ❌ Seller capek reply review 1-1
- ❌ Review negative gak ditanggapi → customer kabur
- ❌ Gak tau sentimen review (positive/negative/mixed)
- ❌ Gak ada alert untuk review critical

**Solusi:**
- ✅ **Bulk Review Classification** - Klasifikasi 100+ review sekaligus
- ✅ **Auto-Reply Draft** - Generate reply empathetic otomatis
- ✅ **Alert System** - Notifikasi untuk review critical
- ✅ **Dashboard** - Visualisasi sentimen review

---

## 🎯 Fitur Utama

### 1. 🔍 Review Classifier

Klasifikasi review TikTok Shop dengan confidence score.

**Input:**
```
"Barang sampe pecah:("
```

**Output:**
```json
{
  "sentiment": "negative",
  "confidence": 95,
  "key_issues": ["Barang rusak saat pengiriman"],
  "recommended_action": "Tawarkan penggantian"
}
```

### 2. 💬 Reply Drafter

Generate reply empathetic 50-100 karakter.

**Input:**
```
Review: "Barang sampe pecah:("
Sentiment: negative
```

**Output:**
```json
{
  "reply_text": "Maaf barang pecah 🙏 DM admin untuk ganti gratis ya! 😊",
  "tone": "empathetic",
  "follow_up_needed": true
}
```

### 3. 📦 Bulk Review Manager

Proses 100+ review sekaligus.

**Features:**
- Bulk classification
- Auto-generate replies
- Alert untuk review critical
- Export report (JSON/Text)

**Contoh:**
```python
from ai_engine import BulkReviewManager

manager = BulkReviewManager()
reviews = ["Review 1", "Review 2", "Review 3"]

result = manager.classify_bulk_reviews(reviews)

print(f"Total: {result['stats']['total']}")
print(f"Positive: {result['stats']['positive_rate']}%")
print(f"Negative: {result['stats']['negative_rate']}%")
print(f"Alerts: {len(result['alerts'])}")
```

### 4. 🚨 Alert System

Notifikasi otomatis untuk review critical.

**Alert Levels:**
- 🔴 **CRITICAL**: Barang palsu, scam, bahaya
- 🟠 **HIGH**: Review negative dengan confidence >85%
- 🟡 **MEDIUM**: Review negative dengan confidence >70%
- 🟢 **LOW**: Review mixed

**Contoh Alert:**
```
[CRITICAL] Review #4: Barang palsu, Peringatan untuk tidak membeli
[HIGH] Review #1: Barang pecah saat sampai
```

---

## 🚀 Quick Start

### Install

```bash
git clone https://github.com/hadijayyy/rankup-ai.git
cd rankup-ai
pip install -r requirements.txt
```

### Setup Environment

```bash
# Copy template
cp .env.example .env

# Edit .env
OPENCODE_GO_API_KEY=your_k...n
```

### Basic Usage

```python
from ai_engine import ReviewClassifier, ReplyDrafter, BulkReviewManager

# 1. Single Review Classification
classifier = ReviewClassifier()
result = classifier.classify_review("Barang sampe pecah:(")
print(f"Sentiment: {result['sentiment']} ({result['confidence']}%)")

# 2. Single Reply Draft
drafter = ReplyDrafter()
review_data = {"text": "Barang sampe pecah:(", "rating": 1}
reply = drafter.draft_reply(review_data)
print(f"Reply: {reply['reply_text']}")

# 3. Bulk Processing
manager = BulkReviewManager()
reviews = ["Review 1", "Review 2", "Review 3"]
result = manager.classify_bulk_reviews(reviews)
print(f"Processed {result['total_reviews']} reviews")
```

---

## 📊 Contoh Output

### Review Classification

```
📊 REVIEW ANALYSIS REPORT
==================================================
Total Reviews: 5
Positive Rate: 20.0%
Negative Rate: 40.0%
Average Confidence: 93.0%

SENTIMENT DISTRIBUTION:
  Positive: 1
  Negative: 2
  Neutral: 2
  Mixed: 0

ALERTS (2 critical reviews):
  [HIGH] Review #1: Barang pecah saat sampai
  [CRITICAL] Review #4: Barang palsu, Peringatan untuk tidak membeli
```

### Reply Examples

| Review | Reply | Tone |
|--------|-------|------|
| "Barang pecah:(" | "Maaf barang pecah 🙏 DM admin untuk ganti gratis ya! 😊" | empathetic |
| "Mantap banget! 🔥" | "Makasih kak! Seneng banget kamu puas! 🫶" | friendly |
| "Barang palsu!!" | "Mohon maaf 🙏 Kami pastikan produk original. DM admin." | empathetic |

---

## 🏗️ Architecture

```
rankup-ai/
├── ai_engine/
│   ├── review_classifier.py    # Klasifikasi sentimen
│   ├── reply_drafter.py        # Generate reply
│   ├── bulk_review_manager.py  # Bulk processing + alerts
│   └── report_generator.py     # Report generation
├── scraper/
│   ├── config.py               # Configuration
│   └── review_scraper.py       # Scrape reviews
├── dashboard/
│   └── notifier.py             # Alert notifications
├── test_integration.py         # Integration tests
└── requirements.txt
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
OPENCODE_GO_API_KEY=your_api_key

# Optional
LLM_MODEL=deepseek-v4-flash
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1500
```

### Config File

```yaml
# config.yaml
llm:
  model: deepseek-v4-flash
  temperature: 0.3
  max_tokens: 1500

alerts:
  enabled: true
  critical_keywords:
    - palsu
    - scam
    - tipu
    - bahaya
```

---

## 🧪 Testing

```bash
# Run integration tests
python test_integration.py

# Run all tests
pytest tests/

# Expected output:
# ✅ PASS - Review Classifier
# ✅ PASS - Reply Drafter
# ✅ PASS - Bulk Review Manager
# 🎯 Result: 4/4 tests passed
```

---

## 💰 Pricing Model

### Target Market
- Seller TikTok Shop Indonesia
- 50+ review/bulan
- Butuh automation

### Harga

| Plan | Harga | Features |
|------|-------|----------|
| **Basic** | Rp 100rb/bulan | 100 reviews, 1 user |
| **Pro** | Rp 200rb/bulan | 500 reviews, 3 users, alerts |
| **Business** | Rp 500rb/bulan | Unlimited, API access |

### Revenue Potential
```
100 users × Rp 200rb = Rp 20 juta/bulan
500 users × Rp 200rb = Rp 100 juta/bulan

Target 1 Milyar = 12-18 bulan
```

---

## 🎯 Kenapa RankUp AI?

| Aspek | RankUp AI | Kompetitor |
|-------|-----------|------------|
| **Harga** | Rp 100-500rb/bulan | $50-100/bulan |
| **Bahasa** | Indonesia native | English only |
| **Fitur** | Review + Reply + Alerts | Basic classification |
| **Support** | WhatsApp/Telegram | Email only |

---

## 🛠️ Tech Stack

- **Language:** Python 3.11
- **LLM:** DeepSeek V4 Flash (via OpenCode-Go)
- **API:** OpenAI-compatible
- **Database:** SQLite (for caching)
- **Notifications:** WhatsApp/Telegram API

---

## 📈 Roadmap

### v1.0 (Current)
- ✅ Review classification
- ✅ Reply drafting
- ✅ Bulk processing
- ✅ Alert system

### v1.1 (Next)
- [ ] Web dashboard
- [ ] WhatsApp/Telegram alerts
- [ ] Export to Google Sheets
- [ ] Analytics dashboard

### v2.0 (Future)
- [ ] Multi-platform (Shopee, Lazada)
- [ ] Auto-post replies
- [ ] Competitor review analysis
- [ ] AI-powered review generation

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 💬 Support

- **Issues:** [GitHub Issues](https://github.com/hadijayyy/rankup-ai/issues)
- **WhatsApp:** +62 812-XXXX-XXXX
- **Email:** support@rankup-ai.id

---

**Built with ❤️ for Indonesian TikTok Shop Sellers**
