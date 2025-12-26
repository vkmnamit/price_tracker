# PricePulse: E-commerce Price Tracker

## Overview
PricePulse is a full-stack price tracking platform for Indian e-commerce, supporting Amazon, Flipkart, Myntra, and Nykaa. It scrapes product data, tracks price history, and provides a modern frontend for search, alerts, and deal discovery.

---

## Project Structure

- `frontend/` — Next.js 16.1.1 app (Turbopack)
- `backend/` — FastAPI server (Python)
- `scraper/` — Scrapy spiders for Amazon, Flipkart, Myntra, Nykaa
- `scheduler/` — (Optional) For automating scrapes

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB running locally (default: `mongodb://localhost:27017`)

### 2. Install Dependencies

#### Backend & Scraper
```bash
cd backend
python -m venv ../venv
source ../venv/bin/activate
pip install -r ../scraper/price_scraper/requirements.txt
pip install fastapi uvicorn pymongo
```

#### Frontend
```bash
cd ../frontend
npm install
```

### 3. Start MongoDB
Make sure MongoDB is running locally.

### 4. Run Scrapy Spiders (to populate database)
```bash
cd ../scraper/price_scraper
../../venv/bin/scrapy crawl amazon_spider
../../venv/bin/scrapy crawl flipkart_spider
../../venv/bin/scrapy crawl myntra_spider
../../venv/bin/scrapy crawl nykaa_spider
```

### 5. Start Backend API
```bash
cd ../../backend
../venv/bin/uvicorn main:app --reload
```

### 6. Start Frontend
```bash
cd ../frontend
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## Features & API Endpoints

- **/products/** — Unified product list (searchable, filterable)
- **/deals/** — Hot deals (price drops, best offers)
- **/history/{product_id}** — Price history for a product
- **/alerts/** — Set price alerts (POST)
- **/notifications/** — Get triggered alerts
- **/search/?q=...** — Search products

### Scraper
- Spiders crawl all categories on Amazon, Flipkart, Myntra, Nykaa
- Data is stored in MongoDB (`price_tracker` database)
- Pipelines handle product, price history, and deal extraction

### Frontend
- Modern Next.js UI (React, Tailwind CSS)
- Search, trending deals, price history charts, alert management
- Comparison across platforms

### Backend
- FastAPI with CORS enabled
- MongoDB aggregation for unified product view
- Price history, deal logic, and alert/notification system

---

## How it Works
1. **Scrapers** crawl all categories and store product/price data in MongoDB.
2. **Backend** serves unified product data, price history, deals, and manages alerts.
3. **Frontend** lets users search, view deals, set alerts, and see price history.

---

## Notes
- For best results, run all spiders regularly (use `scheduler/` or cron jobs).
- The project is for educational/demo use. Respect e-commerce site terms and robots.txt.
- You can extend spiders to add more platforms or richer data.

---

## Authors & Credits
- Built with Next.js, FastAPI, Scrapy, MongoDB
- UI inspired by modern SaaS dashboards

---

## License
MIT
# price_tracker
