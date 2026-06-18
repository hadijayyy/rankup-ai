# 📊 RankUp AI Dashboard

## 🎯 Web Dashboard untuk Review Management

### Fitur Dashboard

1. **Main Page**
   - Total reviews statistics
   - Sentiment distribution (positive/negative/neutral)
   - Alert summary
   - Recent reviews list

2. **Review Analysis**
   - Input single review
   - Input bulk reviews (satu per baris)
   - Real-time classification
   - Auto-generate replies

3. **Alert System**
   - Critical review alerts
   - Priority sorting
   - Action recommendations

4. **API Access**
   - REST API endpoints
   - JSON responses
   - Integration-ready

---

## 🚀 Cara Jalankan

### 1. Install Dependencies

```bash
cd rankup-ai
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy .env
cp .env.example .env

# Edit .env
nano .env

# Isi API key
OPENCODE_GO_API_KEY=sk-4SC...n### 3. Jalankan Dashboard

```bash
python dashboard/app.py
```

### 4. Buka Browser

```
http://localhost:8000
```

---

## 📱 Screenshot

### Main Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 RankUp AI Dashboard                                     │
├─────────────────────────────────────────────────────────────┤
│  Total Reviews: 1,234  │  Positive: 65%  │  Alerts: 12     │
├─────────────────────────────────────────────────────────────┤
│  [Input Box: Masukkan review...]                            │
│  [🔍 Analisis] [📦 Bulk Analisis]                           │
├─────────────────────────────────────────────────────────────┤
│  📝 Recent Reviews              │  🚨 Alerts                 │
│  ─────────────────────────────  │  ───────────────────────  │
│  #1234: "Barang pecah:("       │  [CRITICAL] Review #4     │
│  NEGATIVE (95%)                 │  [HIGH] Review #1         │
│  Reply: "Maaf barang pecah 🙏" │                           │
│                                 │                           │
│  #1233: "Mantap banget! 🔥"   │                           │
│  POSITIVE (98%)                 │                           │
│  Reply: "Makasih kak! 🫶"     │                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000/api
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/classify` | Klasifikasi 1 review |
| POST | `/classify-bulk` | Klasifikasi banyak review |
| GET | `/reviews` | Lihat semua reviews |
| GET | `/alerts` | Lihat semua alerts |
| GET | `/stats` | Lihat statistik |

### Contoh API Call

```bash
# Klasifikasi review
curl -X POST http://localhost:8000/api/classify \
  -H "Content-Type: application/json" \
  -d '{"review": "Barang sampe pecah:("}'

# Response:
{
  "review": "Barang sampe pecah:(",
  "sentiment": "negative",
  "confidence": 95,
  "key_issues": ["Barang rusak"],
  "recommended_action": "Tawarkan penggantian",
  "reply_text": "Maaf barang pecah 🙏 DM admin ya! 😊",
  "reply_tone": "empathetic"
}
```

---

## 🎨 Customization

### Ganti Port

```python
# dashboard/app.py
app.run(host='0.0.0.0', port=8080)  # Ganti port
```

### Ganti Theme

Edit file `dashboard/templates/index.html`:
- Ganti warna di bagian `<style>`
- Ganti logo di bagian `<header>`
- Ganti teks sesuai kebutuhan

### Tambah Fitur

1. Buat file baru di `dashboard/`
2. Tambah route di `app.py`
3. Buat template HTML baru
4. Restart dashboard

---

## 🐛 Troubleshooting

### Masalah: Port sudah dipakai

```bash
# Cari process yang pakai port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Masalah: Module not found

```bash
# Pastikan di folder rankup-ai
cd rankup-ai

# Install dependencies
pip install -r requirements.txt
```

### Masalah: API key error

```bash
# Cek .env file
cat .env

# Pastikan API key benar
OPENCODE_GO_API_KEY=sk-4SC...n---

## 📞 Support

- **WhatsApp:** +62 812-XXXX-XXXX
- **Email:** support@rankup-ai.id
- **GitHub:** https://github.com/hadijayyy/rankup-ai/issues

---

**Last Updated:** Juni 2026
**Version:** 1.0.0
