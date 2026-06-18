# 🚀 RankUp AI

**AI-Powered TikTok Shop Listing Optimization + Review Management**

> "Naikin ranking toko lo — listing optimizer + review manager"

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| **Listing Optimizer** | AI analyzes & optimizes TikTok Shop product listings |
| **Review Manager** | AI classifies reviews & drafts replies automatically |
| **Competitor Tracker** | Monitor competitor prices & strategies |
| **Weekly Reports** | Automated intelligence reports via email |
| **Dashboard** | Google Sheets dashboard for all data |

---

## 📦 Project Structure

```
rankup-ai/
├── scraper/              # Data collection
│   ├── config.py         # Global settings
│   ├── tiktok_scraper.py # Product listing scraper
│   └── review_scraper.py # Review scraper
├── ai_engine/            # AI processing
│   ├── listing_analyzer.py    # Analyze listing quality
│   ├── listing_optimizer.py   # Optimize listings
│   ├── review_classifier.py   # Classify reviews
│   ├── reply_drafter.py       # Draft review replies
│   └── report_generator.py    # Generate reports
├── dashboard/            # Output & notifications
│   ├── sheets_manager.py # Google Sheets integration
│   ├── report_formatter.py # Format reports
│   └── notifier.py       # Email/WhatsApp notifications
├── orchestrator/         # Pipeline coordination
│   ├── pipeline.py       # Main pipeline
│   ├── client_manager.py # Client management
│   └── scheduler.py      # Cron scheduler
├── data/                 # Client data
├── config.yaml           # Configuration
└── requirements.txt      # Dependencies
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/ubuntu/rankup-ai
pip install -r requirements.txt
playwright install chromium
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-opencode-go-api-key"
export GOOGLE_SERVICE_ACCOUNT_JSON="/path/to/service-account.json"
export SMTP_EMAIL="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

### 3. Add a Client

```python
from orchestrator.client_manager import ClientManager

cm = ClientManager()
client = cm.add_client(
    name="Toko Jaya",
    tiktok_shop_url="https://www.tiktok.com/@tokojaya/shop",
    email="owner@tokojaya.com",
    phone="+62812xxxxxxx"
)
print(f"Client ID: {client['client_id']}")
```

### 4. Run Full Pipeline

```python
import asyncio
from orchestrator.pipeline import RankUpPipeline

pipeline = RankUpPipeline()
asyncio.run(pipeline.run_full_pipeline("client_id_here"))
```

### 5. Run Daily Monitoring

```python
asyncio.run(pipeline.run_daily_pipeline("client_id_here"))
```

---

## 💰 Pricing Packages

| Package | Price | Includes |
|---------|-------|----------|
| **Starter** | $150 | AI listing optimization |
| **Growth** | $400 | Listing + review monitoring |
| **Pro** | $800 | Full suite + competitor analysis |

---

## ⚙️ Tech Stack

- **Scraper:** Python + Playwright (async)
- **AI:** DeepSeek V4 Flash (OpenAI-compatible API)
- **Dashboard:** Google Sheets (gspread)
- **Notifications:** Gmail SMTP + WhatsApp
- **Scheduler:** APScheduler

---

## 📊 Automation Schedule

| Task | Frequency | Auto |
|------|-----------|------|
| Scrape products | 1x/month | ✅ |
| Optimize listings | 1x/month | ✅ |
| Scrape reviews | Daily | ✅ |
| Classify reviews | Daily | ✅ |
| Draft replies | Daily | ✅ |
| Weekly report | 1x/week | ✅ |
| Quality check | 1-2x/week | ⚠️ Manual |

---

## 🎯 Niche

**TikTok Shop sellers** — beginner sellers yang butuh bantuan optimize listing + manage reviews.

---

*Built with ❤️ by RankUp AI*
