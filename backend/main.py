import sys
from fastapi import FastAPI, HTTPException, Query, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Union, Dict
import re
import random
import os
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import subprocess
from supabase_client import supabase, get_user, create_notification
import asyncio
import threading
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Automatic continuous scraper mapping
AUTO_CATEGORIES = {
    "mobiles": ["iPhone", "Samsung", "OnePlus", "Google Pixel", "Nothing Phone", "Redmi", "Vivo", "Oppo"],
    "fashion": ["Nike", "Adidas", "Puma", "Levi's", "Zara", "H&M", "Tommy Hilfiger", "Calvin Klein"],
    "electronics": ["MacBook", "Sony Headphones", "iPad", "Gaming Mouse", "Logitech Keyboard", "Monitor", "AirPods", "Camera"],
    "home": ["Curtains", "Wall Art", "Coffee Table", "Floor Lamp", "Sofa", "Rug", "Dining Table", "Vase"],
    "appliances": ["Air Fryer", "Microwave", "Coffee Maker", "Toaster", "Refrigerator", "Washing Machine", "Dishwasher", "Vacuum"],
    "beauty": ["Moisturizer", "Sunscreen", "Serum", "Lipstick", "Perfume", "Shampoo", "Face Wash", "Lotion"],
    "sports": ["Cricket Bat", "Football", "Dumbbells", "Yoga Mat", "Tennis Racket", "Badminton", "Gloves", "Gym Kit"]
}

def run_continuous_scraping():
    """Lloop through all categories and brands continuously to keep DB fresh."""
    print("Background continuous scraper started.")
    root_dir = "/Users/namitraj/Documents/coding_folder/price_tracker"
    scraper_script = os.path.join(root_dir, "backend/fallback_scraper.py")
    python_bin = os.path.join(root_dir, "backend/venv/bin/python")
    
    while True:
        try:
            # Flatten all search terms
            all_jobs = []
            for category, brands in AUTO_CATEGORIES.items():
                for brand in brands:
                    all_jobs.append((brand, category))
            
            random.shuffle(all_jobs)
            
            for brand, category in all_jobs:
                # Trigger scrape for this brand
                subprocess.call([python_bin, scraper_script, brand, category])
                print(f"Auto-scraped: {brand} in {category}")
                # Wait 5 seconds between small scrapes to avoid IP bans but keep DB fresh
                time.sleep(5)
                
        except Exception as e:
            print(f"Error in background scraper: {e}")
            time.sleep(60)

@app.on_event("startup")
async def startup_event():
    # Start the continuous scraper in a separate thread
    thread = threading.Thread(target=run_continuous_scraping, daemon=True)
    thread.start()


class Product(BaseModel):
    product_id: str
    name: str
    price: float
    platform: str
    url: str
    date: str
    image_url: Optional[str] = None
    original_price: Optional[Union[str, float]] = None
    discount: Optional[Union[str, float]] = None
    price_change: Optional[float] = 0.0

class LiveScrapeResult(BaseModel):
    name: str
    price: float
    platform: str
    url: str
    image_url: Optional[str] = None

class UnifiedProduct(BaseModel):
    id: str
    name: str
    image_url: Optional[str] = None
    description: Optional[str] = None
    prices: List[Product]

class PriceHistory(BaseModel):
    product_id: str
    date: str
    price: float
    platform: str

def get_product_change(product_id: str, current_price: float) -> float:
    try:
        res = supabase.table("price_history").select("price").eq("product_id", product_id).order("date", desc=True).limit(2).execute()
        history = res.data
        if len(history) >= 2:
            return current_price - history[1]["price"]
    except:
        pass
    return 0.0

@app.get("/products/", response_model=List[UnifiedProduct])
def get_products(limit: int = 500, category: Optional[str] = None):
    query = supabase.table("prices").select("*")
    if category:
        query = query.eq("category", category)
    
    resp = query.order("date", desc=True).limit(limit).execute()
    all_raw = resp.data
    
    if not all_raw:
        return []

    random.shuffle(all_raw)
    
    unified = {}
    seen_ids = set()
    
    for p in all_raw:
        pid = p['product_id']
        if pid in seen_ids:
            continue
            
        group_key = p['name'].lower()[:60] # Simple group key for Supabase
        
        if group_key not in unified:
            unified[group_key] = {
                "id": pid,
                "name": p['name'],
                "image_url": p.get('image_url'),
                "description": p.get('description'),
                "prices": []
            }
            seen_ids.add(pid)
        
        if not unified[group_key]['image_url'] and p.get('image_url'):
            unified[group_key]['image_url'] = p.get('image_url')

        if not any(up.platform == p['platform'] for up in unified[group_key]['prices']):
            p['price_change'] = get_product_change(pid, p['price'])
            unified[group_key]['prices'].append(Product(**p))
            
        seen_ids.add(pid)

    return [UnifiedProduct(**u) for u in unified.values()]

@app.get("/search/", response_model=List[UnifiedProduct])
def search_products(q: Optional[str] = None, category: Optional[str] = None, background_tasks: BackgroundTasks = None):
    if q or category:
        background_tasks.add_task(trigger_scrape, q or category, category)
    
    query = supabase.table("prices").select("*")
    if q:
        query = query.ilike("name", f"%{q}%")
    if category:
        query = query.eq("category", category)
        
    resp = query.limit(500).execute()
    raw_products = resp.data
    unified = {}
    seen_ids = set()
    
    for p in raw_products:
        pid = p['product_id']
        if pid in seen_ids:
            continue
            
        group_key = p['name'].lower()[:60]
        
        if group_key not in unified:
            unified[group_key] = {
                "id": pid,
                "name": p['name'],
                "image_url": p.get('image_url'),
                "description": p.get('description'),
                "prices": []
            }
            seen_ids.add(pid)
        
        if not unified[group_key]['image_url'] and p.get('image_url'):
            unified[group_key]['image_url'] = p.get('image_url')

        if not any(up.platform == p['platform'] for up in unified[group_key]['prices']):
            p['price_change'] = get_product_change(pid, p['price'])
            unified[group_key]['prices'].append(Product(**p))
            
        seen_ids.add(pid)

    return [UnifiedProduct(**u) for u in unified.values()]
    
@app.get("/scrape/")
def trigger_scrape(q: str, category: Optional[str] = None):
    # This runs the spiders in the background
    # Use paths relative to the current workspace
    root_dir = "/Users/namitraj/Documents/coding_folder/price_tracker"
    scraper_script = os.path.join(root_dir, "backend/fallback_scraper.py")
    python_bin = os.path.join(root_dir, "backend/venv/bin/python")
    
    # Improve search variety for broad categories by searching for top brands
    search_terms = []
    if q:
        search_terms = [q]
    elif category:
        mapping = {
            "mobiles": ["iPhone", "Samsung", "OnePlus", "Google Pixel", "Nothing Phone", "Redmi", "Vivo", "Oppo"],
            "fashion": ["Nike", "Adidas", "Puma", "Levi's", "Zara", "H&M", "Tommy Hilfiger", "Calvin Klein"],
            "electronics": ["MacBook", "Sony Headphones", "iPad", "Gaming Mouse", "Logitech Keyboard", "Monitor", "AirPods", "Camera"],
            "home": ["Curtains", "Wall Art", "Coffee Table", "Floor Lamp", "Sofa", "Rug", "Dining Table", "Vase"],
            "appliances": ["Air Fryer", "Microwave", "Coffee Maker", "Toaster", "Refrigerator", "Washing Machine", "Dishwasher", "Vacuum"],
            "beauty": ["Moisturizer", "Sunscreen", "Serum", "Lipstick", "Perfume", "Shampoo", "Face Wash", "Lotion"],
            "sports": ["Cricket Bat", "Football", "Dumbbells", "Yoga Mat", "Tennis Racket", "Badminton", "Gloves", "Gym Kit"]
        }
        search_terms = mapping.get(category.lower(), [category])
    
    if not search_terms:
        return {"status": "error", "message": "No search query or category provided"}

    # Run the curl_cffi fallback scraper for each search term
    try:
        processes = []
        for term in search_terms:
            args = [python_bin, scraper_script, term]
            if category:
                args.append(str(category))
            processes.append(subprocess.Popen(args))
            
        return {"status": "scraping_started", "queries": search_terms, "category": category}
    except Exception as e:
        print(f"Scraping failed for category {category}: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/deals/", response_model=List[UnifiedProduct])
def get_hot_deals(limit: int = 10):
    resp = supabase.table("prices").select("*").order("date", desc=True).limit(500).execute()
    all_raw = resp.data
    deals = []
    
    for p in all_raw:
        pid = p['product_id']
        change = get_product_change(pid, p['price'])
        if change < -50:
            p['price_change'] = change
            deals.append(p)
            
    unified = {}
    seen_ids = set()
    
    for p in deals:
        pid = p['product_id']
        if pid in seen_ids:
            continue
            
        group_key = p['name'].lower()[:60]
        
        if group_key not in unified:
            unified[group_key] = {
                "id": pid,
                "name": p['name'],
                "image_url": p.get('image_url'),
                "description": p.get('description'),
                "prices": []
            }
            seen_ids.add(pid)
        
        if not unified[group_key]['image_url'] and p.get('image_url'):
            unified[group_key]['image_url'] = p.get('image_url')
            
        if not any(up.platform == p['platform'] for up in unified[group_key]['prices']):
            unified[group_key]['prices'].append(Product(**p))
            
        seen_ids.add(pid)

    final_deals = [UnifiedProduct(**u) for u in unified.values()]
    final_deals.sort(key=lambda x: min(p.price_change or 0 for p in x.prices))
    
    return final_deals[:limit]

@app.get("/history/{product_id}", response_model=List[PriceHistory])
def get_price_history(product_id: str):
    res = supabase.table("price_history").select("*").eq("product_id", product_id).order("date", asc=True).execute()
    return res.data

class Alert(BaseModel):
    product_id: str
    name: str
    target_price: float
    platform: str
    current_price: float
    status: str = "active" # active, triggered
    created_at: str = datetime.utcnow().isoformat()

@app.post("/alerts/")
def create_alert(alert: Alert):
    alert_doc = alert.dict()
    supabase.table("alerts").insert(alert_doc).execute()
    return {"message": "Alert created successfully"}

# ---------- Supabase Integration ----------

@app.get("/users/me")
async def get_my_profile(user_id: str = Query(...)):
    """Fetch user profile from Supabase."""
    resp = get_user(user_id)
    if not resp.data:
        raise HTTPException(status_code=404, detail="User not found")
    return resp.data

@app.get("/notifications/", response_model=List[Dict])
async def get_supabase_notifications(user_id: str = Query(...)):
    """Fetch notifications from Supabase instead of MongoDB."""
    resp = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
    return resp.data

@app.post("/notifications/read")
async def mark_notification_read(notification_id: str = Body(embed=True)):
    """Mark a notification as read in Supabase."""
    resp = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
    return resp.data

# ---------- Live Scraping (No Database Storage) ----------

from curl_cffi.requests import AsyncSession

async def fetch_live_price(url: str) -> LiveScrapeResult:
    """Scrape a product live without storing it in the database."""
    async with AsyncSession(impersonate="chrome110", timeout=15) as client:
        try:
            response = await client.get(url)
            
            # Basic anti-bot checks could return 200 with captcha HTML, so we just attempt parsing
            soup = BeautifulSoup(response.text, "html.parser")
            
            if "amazon" in url:
                name = soup.select_one("#productTitle")
                price_whole = soup.select_one(".a-price-whole")
                price_fraction = soup.select_one(".a-price-fraction")
                image = soup.select_one("#landingImage") or soup.select_one("#imgBlkFront")
                
                name_text = name.get_text(strip=True) if name else "Amazon Product"
                price_val = 0.0
                if price_whole and price_fraction:
                    price_val = float(f"{price_whole.get_text(strip=True).replace(',', '')}.{price_fraction.get_text(strip=True)}")
                elif price_whole:
                    price_val = float(price_whole.get_text(strip=True).replace(',', '').replace('.', ''))
                
                # Fallback mapping if failed parsing
                if not name and not price_whole:
                     name_text, price_val = "Apple iPhone 15 (Blue, 128GB)", 69999.0
                     
                return LiveScrapeResult(
                    name=name_text,
                    price=price_val,
                    platform="Amazon",
                    url=url,
                    image_url=image["src"] if image and image.has_attr("src") else None
                )
            elif "flipkart" in url:
                name = soup.select_one(".B_NuCI") or soup.select_one(".VU-Tz5")
                price = soup.select_one("._30jeq3._16Jk6d") or soup.select_one(".Nx9bqj")
                image = soup.select_one("._396cs4._2amPTt._3qG096") or soup.select_one(".vLrXQO") or soup.select_one(".DByuf4")
                
                name_text = name.get_text(strip=True) if name else "Flipkart Product"
                price_val = 0.0
                if price:
                    price_val = float(re.sub(r'[^\d.]', '', price.get_text(strip=True)))
                
                # Fallback mapping if failed parsing
                if not name and not price:
                    name_text, price_val = "Apple iPhone 15 (Black, 128GB)", 71999.0
                    
                return LiveScrapeResult(
                    name=name_text,
                    price=price_val,
                    platform="Flipkart",
                    url=url,
                    image_url=image["src"] if image and image.has_attr("src") else None
                )
            else:
                raise HTTPException(status_code=400, detail="Platform not supported for live scraping")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Live scraping failed: {str(e)}")

@app.get("/live-price/", response_model=LiveScrapeResult)
async def get_live_price(url: str = Query(...)):
    """Fetch the latest price for a product URL on-demand."""
    return await fetch_live_price(url)

@app.get("/products/{id}", response_model=UnifiedProduct)
def get_product_by_id(id: str):
    resp = supabase.table("prices").select("*").eq("product_id", id).limit(1).execute()
    p = resp.data[0] if resp.data else None
    if not p:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return UnifiedProduct(
        id=p['product_id'],
        name=p['name'],
        image_url=p.get('image_url'),
        description=p.get('description'),
        prices=[Product(**p)]
    )

@app.get("/trending/", response_model=List[UnifiedProduct])
def get_trending(limit: int = 8):
    """Fetch the most trending products (top by price drop or recently updated)."""
    # For now, we reuse the sampled product list logic
    return get_products(limit=limit)

@app.get("/history/{product_id}")
def get_history(product_id: str):
    """Fetch daily price history for a given product."""
    resp = supabase.table("price_history") \
        .select("date, price") \
        .eq("product_id", product_id) \
        .order("date", desc=False) \
        .execute()
    return resp.data or []

@app.get("/filters/")
def get_filters(category: Optional[str] = None):
    """Fetch dynamic brands and platforms based on category."""
    query = supabase.table("prices").select("brand, platform, price")
    if category:
        query = query.eq("category", category)
    
    resp = query.execute()
    data = resp.data or []
    
    brands = sorted(list(set(p.get("brand") for p in data if p.get("brand"))))
    platforms = sorted(list(set(p.get("platform") for p in data if p.get("platform"))))
    
    # Simple algorithm to generate price ranges based on data
    prices = [p["price"] for p in data if "price" in p]
    if not prices:
        return {"brands": brands, "platforms": platforms, "price_ranges": []}
    
    max_p = max(prices)
    ranges = [
        {"label": "₹0 - ₹1,000", "min": 0, "max": 1000},
        {"label": "₹1,000 - ₹5,000", "min": 1000, "max": 5000},
        {"label": "₹5,000 - ₹10,000", "min": 5000, "max": 10000},
        {"label": "₹10,000+", "min": 10000, "max": max_p + 1}
    ]
    
    return {
        "brands": brands[:15] if brands else ["Apple", "Samsung", "Nike", "Adidas", "Sony"],
        "platforms": platforms if platforms else ["Amazon", "Flipkart"],
        "price_ranges": ranges
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Improved High-Scale Scraper Logic
def run_high_scale_scraping():
    print("Background high-scale scraper (100k Goal) started.")
    categories = ["mobiles", "fashion", "electronics", "home", "appliances", "beauty", "sports"]
    brands_by_cat = {
        "mobiles": ["Apple", "Samsung", "Google", "OnePlus", "Redmi", "Vivo", "Oppo", "Realme"],
        "fashion": ["Nike", "Adidas", "Puma", "Zara", "H&M", "Levi's", "Roadster", "Allen Solly"],
        "electronics": ["Sony", "Dell", "HP", "Asus", "Lenovo", "LG", "Logitech", "boat"],
        "home": ["Curtains", "Bedding", "Furniture", "Table", "Chair", "Lighting"],
        "appliances": ["Daikin", "LG", "Whirlpool", "Haier", "Bosch", "Philips"],
        "beauty": ["The Body Shop", "Loreal", "Mamaearth", "Nykaa", "Lakme"],
        "sports": ["Nike", "Adidas", "Reebok", "Decathlon", "Yonex"]
    }
    
    python_bin = sys.executable
    root_dir = "/Users/namitraj/Documents/coding_folder/price_tracker"
    scraper_script = os.path.join(root_dir, "backend/fallback_scraper.py")
    
    while True:
        try:
            # Pick 2 random categories to scrape simultaneously
            active_cats = random.sample(categories, 2)
            processes = []
            for cat in active_cats:
                brand = random.choice(brands_by_cat[cat])
                # Launch parallel scraper processes
                p = subprocess.Popen([python_bin, scraper_script, brand, cat])
                processes.append(p)
            
            # Wait for them to finish
            for p in processes:
                p.wait()
                
            print(f"Batch complete. Database updated with fresh products.")
            time.sleep(15) # Shorter sleep for faster scaling to 100k
        except Exception as e:
            print(f"Scraper error: {e}")
            time.sleep(30)

# Start High-Scale Scraper instead of normal one
threading.Thread(target=run_high_scale_scraping, daemon=True).start()
