from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import List, Optional, Union
import re
import random
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient("mongodb://localhost:27017/")
db = client["price_tracker"]

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
    history = list(db.price_history.find({"product_id": product_id}).sort("date", -1).limit(2))
    if len(history) >= 2:
        return current_price - history[1]["price"]
    return 0.0

@app.get("/products/", response_model=List[UnifiedProduct])
def get_products(limit: int = 50):
    # Use aggregation to get a truly random sample for diversity
    pipeline = [
        {"$sample": {"size": 1000}}
    ]
    all_raw = list(db.prices.aggregate(pipeline))
    
    if not all_raw:
        return []

    # Although we sampled, we shuffle again to be sure
    random.shuffle(all_raw)
    
    unified = {}
    seen_ids = set()
    
    for p in all_raw:
        if p['product_id'] in seen_ids:
            continue
            
        name_clean = re.sub(r'[^a-zA-Z0-9 ]', '', p['name']).lower().split()
        # Use first 5 words for grouping to be more specific and avoid mismatching categories (e.g. "Apple" vs "Apple Watch")
        group_key = " ".join(name_clean[:5]) if len(name_clean) >= 5 else p['name'].lower()
        
        if group_key not in unified:
            unified[group_key] = {
                "id": p['product_id'],
                "name": p['name'],
                "image_url": p.get('image_url'),
                "description": p.get('description'),
                "prices": []
            }
            seen_ids.add(p['product_id'])
        
        if not unified[group_key]['image_url'] and p.get('image_url'):
            unified[group_key]['image_url'] = p.get('image_url')

        if not any(up.platform == p['platform'] for up in unified[group_key]['prices']):
            p['price_change'] = get_product_change(p['product_id'], p['price'])
            unified[group_key]['prices'].append(Product(**p))

    final_list = [UnifiedProduct(**u) for u in unified.values()]
    random.shuffle(final_list)
    
    return final_list[:limit]

@app.get("/search/", response_model=List[UnifiedProduct])
def search_products(q: str):
    query = {"name": {"$regex": q, "$options": "i"}}
    raw_products = list(db.prices.find(query).limit(100))
    unified = {}
    seen_ids = set()
    
    for p in raw_products:
        if p['product_id'] in seen_ids:
            continue
            
        name_clean = re.sub(r'[^a-zA-Z0-9 ]', '', p['name']).lower().split()
        group_key = " ".join(name_clean[:5]) if len(name_clean) >= 5 else p['name'].lower()
        
        if group_key not in unified:
            unified[group_key] = {
                "id": p['product_id'],
                "name": p['name'],
                "image_url": p.get('image_url'),
                "description": p.get('description'),
                "prices": []
            }
            seen_ids.add(p['product_id'])
        
        if not unified[group_key]['image_url'] and p.get('image_url'):
            unified[group_key]['image_url'] = p.get('image_url')

        if not any(up.platform == p['platform'] for up in unified[group_key]['prices']):
            p['price_change'] = get_product_change(p['product_id'], p['price'])
            unified[group_key]['prices'].append(Product(**p))

    return [UnifiedProduct(**u) for u in unified.values()]

@app.get("/deals/", response_model=List[UnifiedProduct])
def get_hot_deals(limit: int = 10):
    # Fetch products that have a price drop
    # For simplicity, we sample and then check for drops, or better, we look at the last history entry
    # A more efficient way would be to query products where price_change < 0 if we stored that field
    # But for now, let's fetch some latest items and pick the ones with the best drops
    all_raw = list(db.prices.find({}).sort("date", -1).limit(500))
    deals = []
    
    for p in all_raw:
        change = get_product_change(p['product_id'], p['price'])
        if change < -50: # Only significant drops
            p['price_change'] = change
            deals.append(p)
            
    # Group them similarly to get_products
    unified = {}
    seen_ids = set()
    
    for p in deals:
        if p['product_id'] in seen_ids:
            continue
            
        name_clean = re.sub(r'[^a-zA-Z0-9 ]', '', p['name']).lower().split()
        group_key = " ".join(name_clean[:5]) if len(name_clean) >= 5 else p['name'].lower()
        
        if group_key not in unified:
            unified[group_key] = {
                "id": p['product_id'],
                "name": p['name'],
                "image_url": p.get('image_url'),
                "description": p.get('description'),
                "prices": []
            }
            seen_ids.add(p['product_id'])
        
        # If the existing image_url is null, try to update it with the current item's image_url
        if not unified[group_key]['image_url'] and p.get('image_url'):
            unified[group_key]['image_url'] = p.get('image_url')
            
        if not any(up.platform == p['platform'] for up in unified[group_key]['prices']):
            unified[group_key]['prices'].append(Product(**p))

    # Sort by the biggest drop
    final_deals = [UnifiedProduct(**u) for u in unified.values()]
    final_deals.sort(key=lambda x: min(p.price_change or 0 for p in x.prices))
    
    return final_deals[:limit]

@app.get("/history/{product_id}", response_model=List[PriceHistory])
def get_price_history(product_id: str):
    history = list(db.price_history.find({"product_id": product_id}, {"_id": 0}).sort("date", 1))
    return history

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
    db.alerts.insert_one(alert_doc)
    return {"message": "Alert created successfully"}

@app.get("/notifications/")
def get_notifications():
    # Find all active alerts where target_price >= current_price in the latest data
    active_alerts = list(db.alerts.find({"status": "active"}))
    triggered = []
    
    for alert in active_alerts:
        # Get latest price for this product
        latest = db.prices.find_one({"product_id": alert["product_id"]}, sort=[("date", -1)])
        if latest and latest["price"] <= alert["target_price"]:
            triggered.append({
                "product_id": alert["product_id"],
                "name": alert["name"],
                "target_price": alert["target_price"],
                "current_price": latest["price"],
                "platform": latest["platform"]
            })
            # Mark as triggered so we don't notify again
            db.alerts.update_one({"_id": alert["_id"]}, {"$set": {"status": "triggered"}})
            
    return triggered

@app.on_event("shutdown")
def shutdown_event():
    client.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}
