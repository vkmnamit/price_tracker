import sys
from supabase_client import supabase
from curl_cffi.requests import Session
from bs4 import BeautifulSoup
from datetime import datetime
import re
import random



def scrape_amazon(q, category=None):
    print(f"Scraping Amazon for {q}")
    found = False
    with Session(impersonate="chrome110") as session:
        url = f"https://www.amazon.in/s?k={q.replace(' ', '+')}"
        res = session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select('div[data-component-type="s-search-result"]')
        print(f"Found {len(items)} items on Amazon for {q}")

        for item in items[:12]:
            try:
                name_elem = item.select_one("span.a-text-normal") or item.select_one("h2 a span") or item.select_one("h2")
                price_whole = item.select_one("span.a-price-whole") or item.select_one(".a-offscreen") or item.select_one(".a-price")
                url_elem = item.select_one("a.a-link-normal.s-no-outline") or item.select_one("h2 a")
                img_elem = item.select_one(".s-image") or item.select_one("img[data-image-latency]") or item.select_one("img")
                
                img = None
                if img_elem:
                    img = img_elem.get("src") or img_elem.get("data-src") or img_elem.get("srcset", "").split(" ")[0]
                
                if name_elem and price_whole and url_elem and img:
                    name = name_elem.text.strip()
                    brand = name.split()[0] # Extract first word as brand fallback
                    price_text = price_whole.text.replace(',', '').replace('.', '').strip()
                    price_val = float(re.sub(r'[^\d.]', '', price_text) or "0")
                    link = "https://www.amazon.in" + url_elem["href"] if url_elem["href"].startswith("/") else url_elem["href"]
                    product_id = link.split("/dp/")[1].split("/")[0].split("?")[0] if "/dp/" in link else link.split("/")[-1]
                    
                    product_doc = {
                        "product_id": product_id,
                        "name": name,
                        "brand": brand,
                        "price": price_val,
                        "platform": "Amazon",
                        "url": link,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "image_url": img,
                        "original_price": price_val * 1.2, # Mock original
                        "discount": "20% off",
                        "category": category
                    }
                    supabase.table("prices").upsert(product_doc, on_conflict="url").execute()
                    supabase.table("price_history").insert({
                        "product_id": product_id,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "price": price_val,
                        "platform": "Amazon"
                    }).execute()
                    print(f"Saved {name} from Amazon at {price_val}")
                    found = True
                else:
                    if not found:
                         print(f"Skipping Amazon item: name={bool(name_elem)}, price={bool(price_whole)}, url={bool(url_elem)}, img={bool(img)}")
            except Exception as e:
                print(f"Error parsing Amazon item: {e}")
                
    if not found:
        print(f"No real products found for {q} on Amazon.")

def scrape_flipkart(q, category=None):
    print(f"Scraping Flipkart for {q}")
    found = False
    with Session(impersonate="chrome110") as session:
        url = f"https://www.flipkart.com/search?q={q.replace(' ', '+')}"
        res = session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        # Much broader item container search
        items = soup.select("div.cPHDOP") or soup.select("div._1AtVbE") or soup.select("div.sl_pOOi") or soup.find_all("div", {"data-id": True})
        print(f"Found {len(items)} potential items on Flipkart for {q}")

        for item in items[:12]:
            try:
                # Super robust name selection
                name_elem = (item.select_one("div.KzDlHZ") or 
                             item.select_one("a.IRpwCQ") or 
                             item.select_one("a.s1Q9rs") or 
                             item.select_one("div.VU-Tz5") or 
                             item.select_one("div._4rR01T") or
                             item.find('a', title=True) or
                             item.select_one("a.W_N9_X"))
                
                # Robust price selection targeting the currency symbol or specific classes
                price_elem = (item.select_one("div.Nx9bqj") or 
                              item.select_one("div._30jeq3") or 
                              item.select_one("div._16Jk6d") or 
                              item.select_one("div._3I9_wc") or
                              item.find(string=re.compile(r'₹')))
                
                url_elem = item.select_one("a[href]")
                img_elem = (item.select_one("img.DByuf4") or 
                            item.select_one("img._396cs4") or 
                            item.select_one("img.vLrXQO") or 
                            item.find("img", src=True))
                
                img = None
                if img_elem:
                    img = img_elem.get("src") or img_elem.get("data-src") or img_elem.get("srcset", "").split(" ")[0]
                
                if name_elem and price_elem and url_elem and img:
                    name = name_elem.get('title') or name_elem.text.strip()
                    brand = name.split()[0] # Extract first word as brand fallback
                    price_text = re.sub(r'[^\d.]', '', price_elem.text)
                    price_val = float(price_text) if price_text else 0.0
                    link = "https://www.flipkart.com" + url_elem["href"] if url_elem["href"].startswith("/") else url_elem["href"]
                    product_id = item.get("data-id") or link.split("?")[0].split("/")[-1]
                    
                    product_doc = {
                        "product_id": product_id,
                        "name": name,
                        "brand": brand,
                        "price": price_val,
                        "platform": "Flipkart",
                        "url": link,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "image_url": img,
                        "original_price": price_val * 1.25,
                        "discount": "25% off",
                        "category": category
                    }
                    supabase.table("prices").upsert(product_doc, on_conflict="url").execute()
                    supabase.table("price_history").insert({
                        "product_id": product_id,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "price": price_val,
                        "platform": "Flipkart"
                    }).execute()
                    print(f"Saved {name} from Flipkart at {price_val}")
                    found = True
                else:
                    if not found:
                        print(f"Skipping Flipkart item: name={bool(name_elem)}, price={bool(price_elem)}, url={bool(url_elem)}, img={bool(img)}")
            except Exception as e:
                print(f"Error parsing Flipkart item: {e}")
                
    if not found:
        print(f"No real products found for {q} on Flipkart.")

def scrape_myntra(q, category=None):
    print(f"Scraping Myntra for {q}")
    found = False
    with Session(impersonate="chrome110") as session:
        url = f"https://www.myntra.com/{q.replace(' ', '-')}"
        res = session.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select("li.product-base")
        print(f"Found {len(items)} items on Myntra for {q}")

        for item in items[:12]:
            try:
                brand_elem = item.select_one("h3.product-brand")
                product_elem = item.select_one("h4.product-product")
                price_elem = item.select_one("span.product-discountedPrice") or item.select_one("div.product-price")
                url_elem = item.select_one("a")
                img_elem = item.select_one("img")
                
                img = None
                if img_elem:
                    img = img_elem.get("src") or img_elem.get("data-src")
                
                if brand_elem and price_elem and url_elem and img:
                    brand = brand_elem.text.strip()
                    name = brand + " " + (product_elem.text.strip() if product_elem else "")
                    price_text = re.sub(r'[^\d.]', '', price_elem.text)
                    price_val = float(price_text) if price_text else 0.0
                    link = "https://www.myntra.com/" + url_elem["href"] if not url_elem["href"].startswith("http") else url_elem["href"]
                    product_id = link.split("/")[-2]
                    
                    product_doc = {
                        "product_id": f"myntra_{product_id}",
                        "name": name,
                        "brand": brand,
                        "price": price_val,
                        "platform": "Myntra",
                        "url": link,
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "image_url": img,
                        "original_price": price_val * 1.4,
                        "discount": "40% off",
                        "category": category
                    }
                    supabase.table("prices").upsert(product_doc, on_conflict="url").execute()
                    supabase.table("price_history").insert({
                        "product_id": f"myntra_{product_id}",
                        "date": datetime.today().strftime('%Y-%m-%d'),
                        "price": price_val,
                        "platform": "Myntra"
                    }).execute()
                    print(f"Saved {name} from Myntra at {price_val}")
                    found = True
            except Exception as e:
                print(f"Error parsing Myntra item: {e}")
                
    if not found:
        print(f"No real products found for {q} on Myntra.")

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "laptop"
    category = sys.argv[2] if len(sys.argv) > 2 else None
    print(f"Starting fallback scraper for '{q}' and category '{category}'")
    scrape_amazon(q, category)
    scrape_flipkart(q, category)
    if category == "fashion":
        scrape_myntra(q, category)
    print("Done")
