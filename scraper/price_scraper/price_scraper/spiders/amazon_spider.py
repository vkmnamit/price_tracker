
from scrapy import Spider
from datetime import datetime
from price_scraper.items import (ProductItem, PriceHistoryItem, PlatformItem,
                                 CategoryItem, ReviewItem, SellerItem, StockItem,
                                 DiscountItem)
class AmazonSpider(Spider):
    name = "amazon_spider"
    allowed_domains = ["amazon.com"]
    start_urls = [
        "https://www.amazon.com/s?k=laptops",
    ]

    def parse(self, response):
        products = response.css("div.s-main-slot div.s-result-item")
        for product in products:
            product_id = product.attrib.get("data-asin")
            name = product.css("h2 a span::text").get()
            price_whole = product.css("span.a-price-whole::text").get()
            price_fraction = product.css("span.a-price-fraction::text").get()
            price = None
            if price_whole and price_fraction:
                price = f"{price_whole}.{price_fraction}"
            url = product.css("h2 a::attr(href)").get()
            full_url = response.urljoin(url) if url else None

            if product_id and name and price:
                product_item = ProductItem(
                    product_id=product_id,
                    name=name,
                    price=price,
                    platform="Amazon",
                    url=full_url,
                    date=datetime.utcnow().date()
                )
                yield product_item

                price_history_item = PriceHistoryItem(
                    product_id=product_id,
                    date=datetime.utcnow().date(),
                    price=price,
                    platform="Amazon"
                )
                yield price_history_item

        next_page = response.css("ul.a-pagination li.a-last a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
        # Additional parsing for categories, reviews, sellers, stock, discounts can be added here
        # For brevity, only product and price history items are implemented in this example.
        # Example for parsing categories
        categories = response.css("div#departments a")
        for category in categories:
            category_name = category.css("::text").get()
            category_url = category.attrib.get("href")
            full_category_url = response.urljoin(category_url) if category_url else None

            if category_name and full_category_url:
                category_item = CategoryItem(
                    category_name=category_name,
                    category_url=full_category_url,
                    parent_category=None,
                    platform="Amazon"
                )
                yield category_item
        # Example for parsing platform info
        platform_item = PlatformItem(
            platform_name="Amazon",
            platform_url="https://www.amazon.com",
            country="US"
        )
        yield platform_item 

        # Note: ReviewItem, SellerItem, StockItem, and DiscountItem parsing would typically require navigating to individual product pages.
            

