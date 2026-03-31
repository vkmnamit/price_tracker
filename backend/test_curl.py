from curl_cffi import requests
from bs4 import BeautifulSoup
import re

def test_flipkart():
    print("Testing Flipkart...")
    response = requests.get('https://www.flipkart.com/apple-iphone-15-black-128-gb/p/itm706abb30e5416', impersonate="chrome110")
    print("Status:", response.status_code)
    soup = BeautifulSoup(response.text, "html.parser")
    print("Page body excerpt:", response.text[5000:6000])
    
    print("Title:", soup.title.string if soup.title else "No title")

def test_amazon():
    print("Testing Amazon...")
    response = requests.get('https://www.amazon.in/dp/B0CHX1W1XY', impersonate="chrome110")
    print("Status:", response.status_code)
    soup = BeautifulSoup(response.text, "html.parser")
    name = soup.select_one("#productTitle")
    price_whole = soup.select_one(".a-price-whole")
    print("Name:", name.get_text(strip=True) if name else "Not found")
    print("Price:", price_whole.get_text(strip=True) if price_whole else "Not found")

test_flipkart()
test_amazon()
