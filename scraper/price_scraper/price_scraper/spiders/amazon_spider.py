
from scrapy import Spider
from datetime import datetime
from price_scraper.items import (ProductItem, PriceHistoryItem, PlatformItem,
                                 CategoryItem, ReviewItem, SellerItem, StockItem,
                                 DiscountItem)
class AmazonSpider(Spider):
    name = "amazon_spider"
    allowed_domains = ["amazon.com"]
    start_urls = [
        "https://www.amazon.com/s?k=smartwatches",
        "https://www.amazon.com/s?k=mens+watches",
        "https://www.amazon.com/s?k=womens+watches",
        "https://www.amazon.com/s?k=sneakers",
        "https://www.amazon.com/s?k=running+shoes",
        "https://www.amazon.com/s?k=gaming+monitors",
        "https://www.amazon.com/s?k=bluetooth+speakers",
        "https://www.amazon.com/s?k=tablets",
        "https://www.amazon.com/s?k=dslr+cameras",
    ]

    def parse(self, response):
        # Target any div that has a data-asin attribute
        products = response.css("div[data-asin]")
        
        self.logger.info(f"Found {len(products)} products on {response.url}")

        for product in products:
            product_id = product.attrib.get("data-asin")
            if not product_id:
                continue

            # Multiple title selectors as fallbacks
            name = product.css("h2 a span::text").get() or \
                   product.css("h2 span::text").get() or \
                   product.css("span.a-size-medium::text").get() or \
                   product.css("span.a-size-base-plus::text").get() or \
                   product.css("span.a-text-normal::text").get()
            
            # Image extraction with fallbacks
            image_url = product.css("img.s-image::attr(src)").get() or \
                        product.css("img[data-image-latency]::attr(src)").get() or \
                        product.css("img::attr(src)").get()

            # Price extraction logic
            price = None
            price_whole = product.css("span.a-price-whole::text").get()
            price_fraction = product.css("span.a-price-fraction::text").get()
            
            if price_whole:
                price_whole = price_whole.strip().rstrip('.')
                price = price_whole
                if price_fraction:
                    price = f"{price_whole}.{price_fraction}"
            
            if not price:
                price = product.css("span.a-price span.a-offscreen::text").get()
            
            # Original Price (for discount calculation)
            original_price = product.css("span.a-price.a-text-price span.a-offscreen::text").get() or \
                             product.css("span.a-letter-space + span.a-offscreen::text").get()

            url = product.css("h2 a::attr(href)").get() or \
                  product.css("a.a-link-normal::attr(href)").get() or \
                  product.css("a.a-text-normal::attr(href)").get()
            full_url = response.urljoin(url) if url else None

            if product_id and name and price:
                product_item = ProductItem(
                    product_id=product_id,
                    name=name.strip(),
                    price=price,
                    platform="Amazon",
                    url=full_url,
                    date=datetime.utcnow().date(),
                    image_url=image_url,
                    original_price=original_price
                )
                yield product_item

                price_history_item = PriceHistoryItem(
                    product_id=product_id,
                    date=datetime.utcnow().date(),
                    price=price,
                    platform="Amazon"
                )
                yield price_history_item
            else:
                if product_id:
                    self.logger.debug(f"Missing data for ASIN {product_id}: name={name}, price={price}, url={full_url}")

        next_page = response.css("ul.a-pagination li.a-last a::attr(href)").get() or \
                    response.css("a.s-pagination-next::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

        categories = response.css("div#departments a")
        for category in categories:
            category_name = category.css("::text").get()
            category_url = category.attrib.get("href")
            full_category_url = response.urljoin(category_url) if category_url else None

            if category_name and full_category_url:
                yield CategoryItem(
                    category_name=category_name,
                    category_url=full_category_url,
                    parent_category=None,
                    platform="Amazon"
                )

        yield PlatformItem(
            platform_name="Amazon",
            platform_url="https://www.amazon.com",
            country="US"
        )
 

        # Note: ReviewItem, SellerItem, StockItem, and DiscountItem parsing would typically require navigating to individual product pages.
            

