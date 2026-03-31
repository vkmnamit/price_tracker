import os
import random
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv() # Load from .env file

from supabase_client import supabase

def migrate_mongo_to_supabase():
    print("Connecting to MongoDB...")
    mongo_client = MongoClient("mongodb://localhost:27017/")
    db = mongo_client["price_tracker"]
    
    # 1. Migrate Prices
    print("Fetching prices from MongoDB...")
    mongo_prices = list(db.prices.find())
    print(f"Found {len(mongo_prices)} products. Migrating to Supabase...")
    
    # Process in batches of 100 for Supabase stability
    batch_size = 100
    for i in range(0, len(mongo_prices), batch_size):
        batch = mongo_prices[i:i+batch_size]
        cleaned_batch = []
        for p in batch:
            # Remove MongoDB internal _id field
            if '_id' in p: del p['_id']
            # Ensure price is a float
            p['price'] = float(p.get('price') or 0.0)
            p['original_price'] = float(p.get('original_price') or p.get('price') or 0.0)
            cleaned_batch.append(p)
            
        try:
            supabase.table("prices").upsert(cleaned_batch, on_conflict="url").execute()
            print(f"Migrated prices up to {i + len(batch)}")
        except Exception as e:
            print(f"Batch {i} failed: {e}")

    # 2. Migrate Price History
    print("Fetching price history from MongoDB...")
    history = list(db.price_history.find())
    print(f"Found {len(history)} history entries. Migrating to Supabase...")
    
    for i in range(0, len(history), batch_size):
        batch = history[i:i+batch_size]
        cleaned_batch = []
        for h in batch:
            if '_id' in h: del h['_id']
            h['price'] = float(h.get('price', 0.0))
            cleaned_batch.append(h)
            
        try:
            supabase.table("price_history").insert(cleaned_batch).execute()
            print(f"Migrated history up to {i + len(batch)}")
        except Exception as e:
            print(f"History Batch {i} failed: {e}")

    print("Migration complete!")

if __name__ == "__main__":
    # Ensure environment variables are loaded
    # Supabase credentials should be in the .env file already
    migrate_mongo_to_supabase()
