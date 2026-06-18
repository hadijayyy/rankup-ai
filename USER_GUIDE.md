# 📚 RankUp AI - Step by Step Guide

## 🎯 Panduan Lengkap Penggunaan RankUp AI Review Bot

---

## 📋 Table of Contents

1. [Instalasi](#1-instalasi)
2. [Konfigurasi](#2-konfigurasi)
3. [Cara Pakai Basic](#3-cara-pakai-basic)
4. [Bulk Processing](#4-bulk-processing)
5. [Alert System](#5-alert-system)
6. [Dashboard](#6-dashboard)
7. [API Usage](#7-api-usage)
8. [Tips & Tricks](#8-tips--tricks)

---

## 1. Instalasi

### Prasyarat
- Python 3.11+
- OpenCode-Go API key (gratis trial 7 hari)
- Terminal/Command Prompt

### Langkah Instalasi

```bash
# 1. Clone repository
git clone https://github.com/hadijayyy/rankup-ai.git

# 2. Masuk ke folder
cd rankup-ai

# 3. Buat virtual environment
python -m venv venv

# 4. Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Setup environment variables
cp .env.example .env
```

---

## 2. Konfigurasi

### Setup API Key

```bash
# Edit file .env
nano .env

# Isi dengan API key Anda:
OPENCODE_GO_API_KEY=sk-4SC...fcxV
```

### Dapatkan API Key

1. Buka https://opencode.ai/auth
2. Daftar akun gratis
3. Pilih paket "Go" ($10/bulan)
4. Copy API key
5. Paste ke file `.env`

### Konfigurasi Lainnya

```bash
# .env (opsional)
LLM_MODEL=deepseek-v4-flash
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=1500
LOG_LEVEL=INFO
```

---

## 3. Cara Pakai Basic

### 3.1 Klasifikasi 1 Review

```python
from ai_engine import ReviewClassifier

# Inisialisasi
classifier = ReviewClassifier()

# Klasifikasi review
review = "Barang sampe pecah:("
result = classifier.classify_review(review)

# Lihat hasil
print(f"Sentimen: {result['sentiment']}")
print(f"Confidence: {result['confidence']}%")
print(f"Masalah: {result['key_issues']}")
print(f"Aksi: {result['recommended_action']}")
```

**Output:**
```
Sentimen: negative
Confidence: 95%
Masalah: ['Barang rusak saat pengiriman']
Aksi: Tawarkan penggantian
```

### 3.2 Generate Reply

```python
from ai_engine import ReplyDrafter

# Inisialisasi
drafter = ReplyDrafter()

# Data review
review_data = {
    "text": "Barang sampe pecah:(",
    "rating": 1,
    "sentiment": "negative"
}

# Generate reply
result = drafter.draft_reply(review_data)

# Lihat hasil
print(f"Reply: {result['reply_text']}")
print(f"Tone: {result['tone']}")
print(f"Follow-up: {result['follow_up_needed']}")
```

**Output:**
```
Reply: Maaf barang pecah 🙏 DM admin untuk ganti gratis ya! 😊
Tone: empathetic
Follow-up: True
```

---

## 4. Bulk Processing

### 4.1 Klasifikasi Banyak Review

```python
from ai_engine import BulkReviewManager

# Inisialisasi
manager = BulkReviewManager()

# List reviews
reviews = [
    "Barang sampe pecah:(",
    "MANTAAAAP BANGET!!! 🔥🔥🔥",
    "Biasa aja sih, gak ada efek",
    "BARANG PALSU!! Jangan beli!!!",
    "Pengiriman cepat, packaging ok"
]

# Proses bulk
result = manager.classify_bulk_reviews(reviews)

# Lihat statistik
print(f"Total: {result['stats']['total']}")
print(f"Positive: {result['stats']['positive_rate']}%")
print(f"Negative: {result['stats']['negative_rate']}%")
print(f"Alerts: {len(result['alerts'])}")
```

**Output:**
```
Total: 5
Positive: 20.0%
Negative: 40.0%
Alerts: 2
```

### 4.2 Lihat Detail Setiap Review

```python
# Lihat semua review yang sudah diklasifikasi
for review in result['reviews']:
    print(f"#{review['id']}: {review['text'][:50]}...")
    print(f"  Sentimen: {review['sentiment']} ({review['confidence']}%)")
    print(f"  Reply: {review.get('reply_text', 'N/A')[:60]}")
    print()
```

**Output:**
```
#1: Barang sampe pecah:(...
  Sentimen: negative (95%)
  Reply: Maaf barang pecah 🙏 DM admin untuk ganti gratis ya! 😊

#2: MANTAAAAP BANGET!!! 🔥🔥🔥...
  Sentimen: positive (95%)
  Reply: Makasih kak! Seneng banget kamu puas! 🫶

#3: Biasa aja sih, gak ada efek...
  Sentimen: neutral (90%)
  Reply: Makasih reviewnya!Produk butuh waktu pemakaian...
```

---

## 5. Alert System

### 5.1 Lihat Alerts

```python
# Alerts untuk review critical
alerts = result['alerts']

for alert in alerts:
    print(f"[{alert['level'].upper()}] Review #{alert['review_id']}")
    print(f"  Issues: {alert['issues']}")
    print(f"  Action: {alert['action_needed']}")
    print()
```

**Output:**
```
[HIGH] Review #1
  Issues: ['Barang pecah saat sampai']
  Action: Hubungi reviewer, tawarkan penggantian

[CRITICAL] Review #4
  Issues: ['Barang palsu', 'Peringatan untuk tidak membeli']
  Action: Prioritas tinggi - investigasi segera
```

### 5.2 Alert Levels

| Level | Kondisi | Waktu Response |
|-------|---------|----------------|
| 🔴 CRITICAL | Barang palsu, scam, bahaya | < 1 jam |
| 🟠 HIGH | Negative, confidence >85% | < 4 jam |
| 🟡 MEDIUM | Negative, confidence >70% | < 24 jam |
| 🟢 LOW | Mixed sentiment | < 48 jam |

---

## 6. Dashboard

### 6.1 Jalankan Dashboard

```bash
# Jalankan web dashboard
python dashboard/app.py

# Buka browser
# http://localhost:8000
```

### 6.2 Fitur Dashboard

**Main Page:**
- Total reviews
- Sentiment distribution (pie chart)
- Alert summary
- Recent reviews

**Review Management:**
- Filter by sentiment
- Search reviews
- Bulk reply
- Export to CSV

**Alerts Page:**
- Real-time alerts
- Priority sorting
- Action buttons
- History

**Settings:**
- API configuration
- Alert thresholds
- Notification settings
- User management

### 6.3 Screenshot Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  📊 RankUp AI Dashboard                                     │
├─────────────────────────────────────────────────────────────┤
│  Total Reviews: 1,234  │  Positive: 65%  │  Alerts: 12     │
├─────────────────────────────────────────────────────────────┤
│  [Pie Chart: Sentiment Distribution]                        │
│                                                             │
│  Recent Reviews:                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ #1234: "Barang pecah:(" - NEGATIVE (95%)            │  │
│  │ Reply: "Maaf barang pecah 🙏 DM admin ya! 😊"       │  │
│  │ [Reply] [Edit] [Delete]                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ #1233: "Mantap banget! 🔥" - POSITIVE (98%)         │  │
│  │ Reply: "Makasih kak! Seneng kamu puas! 🫶"          │  │
│  │ [Reply] [Edit] [Delete]                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. API Usage

### 7.1 REST API Endpoints

```bash
# Base URL
http://localhost:8000/api

# Endpoints
POST /classify          # Klasifikasi 1 review
POST /classify-bulk     # Klasifikasi banyak review
POST /draft-reply       # Generate reply
GET  /reviews           # Lihat semua reviews
GET  /alerts            # Lihat alerts
GET  /stats             # Lihat statistik
```

### 7.2 Contoh API Calls

```bash
# Klasifikasi review
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"review": "Barang sampe pecah:("}'

# Response:
{
  "sentiment": "negative",
  "confidence": 95,
  "key_issues": ["Barang rusak"],
  "recommended_action": "Tawarkan penggantian"
}
```

```bash
# Bulk classify
curl -X POST http://localhost:8000/api/classify-bulk \
  -H "Content-Type: application/json" \
  -d '{"reviews": ["Review 1", "Review 2", "Review 3"]}'

# Response:
{
  "total": 3,
  "reviews": [...],
  "stats": {...},
  "alerts": [...]
}
```

```bash
# Draft reply
curl -X POST http://localhost:8000/api/draft-reply \
  -H "Content-Type: application/json" \
  -d '{"review": "Barang pecah:(", "sentiment": "negative"}'

# Response:
{
  "reply_text": "Maaf barang pecah 🙏 DM admin ya! 😊",
  "tone": "empathetic",
  "follow_up_needed": true
}
```

---

## 8. Tips & Tricks

### 8.1 Optimasi Hasil

```python
# Gunakan product_info untuk reply yang lebih personal
product_info = {
    "title": "Serum Vitamin C",
    "price": "Rp 89.000"
}

result = drafter.draft_reply(review_data, product_info=product_info)
# Reply akan lebih personal dan relevan
```

### 8.2 Export Report

```python
# Export ke JSON
report_json = manager.export_report(format="json")

# Export ke text
report_text = manager.export_report(format="text")

# Simpan ke file
with open("report.txt", "w") as f:
    f.write(report_text)
```

### 8.3 Filter Reviews

```python
# Filter hanya negative reviews
negative_reviews = [
    r for r in result['reviews'] 
    if r['sentiment'] == 'negative'
]

# Filter high confidence
high_confidence = [
    r for r in result['reviews'] 
    if r['confidence'] > 90
]
```

### 8.4 Automate with Cron

```bash
# Jalankan setiap jam
0 * * * * cd /home/ubuntu/rankup-ai && python auto_check.py

# auto_check.py
from ai_engine import BulkReviewManager
import json

manager = BulkReviewManager()

# Scrape reviews baru
reviews = scrape_new_reviews()  # Implement sendiri

# Proses
result = manager.classify_bulk_reviews(reviews)

# Kirim alert via WhatsApp
if result['alerts']:
    send_whatsapp_alert(result['alerts'])
```

---

## 🆘 Troubleshooting

### Masalah: API Key Error

```
Error: Missing credentials
```

**Solusi:**
```bash
# Cek .env file
cat .env

# Pastikan API key benar
OPENCODE_GO_API_KEY=sk-4SC...fcxV
```

### Masalah: Empty Reply

```
Reply: "" (kosong)
```

**Solusi:**
- Cek koneksi internet
- Increase max_tokens di config
- Coba review yang lebih pendek

### Masalah: Slow Response

```
Response time > 10 detik
```

**Solusi:**
- Cek koneksi internet
- Gunakan server yang lebih dekat
- Cache hasil yang sering diakses

---

## 📞 Support

- **WhatsApp:** +62 812-XXXX-XXXX
- **Email:** support@rankup-ai.id
- **GitHub:** https://github.com/hadijayyy/rankup-ai/issues

---

**Last Updated:** Juni 2026
**Version:** 1.0.0
