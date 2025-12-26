from scrapy import Spider
from datetime import datetime
from price_scraper.items import (
    ProductItem, PriceHistoryItem, PlatformItem, CategoryItem,
    ReviewItem, SellerItem, StockItem, DiscountItem
)
class MyntraSpider(Spider):
    name = "myntra_spider"
    allowed_domains = ["myntra.com"]
    def __init__(self, query=None, *args, **kwargs):
        super(MyntraSpider, self).__init__(*args, **kwargs)
        if query:
            self.start_urls = [f"https://www.myntra.com/{query}"]
        else:
            self.start_urls = [
                "https://www.myntra.com/men-tshirts",
                "https://www.myntra.com/women-tshirts",
                "https://www.myntra.com/women-dresses",
                "https://www.myntra.com/men-jeans",
                "https://www.myntra.com/women-jeans",
                "https://www.myntra.com/men-casual-shoes",
                "https://www.myntra.com/women-casual-shoes",
                "https://www.myntra.com/watches",
                "https://www.myntra.com/headphones",
                "https://www.myntra.com/men-ethnic-wear",
                "https://www.myntra.com/women-ethnic-wear",
                "https://www.myntra.com/handbags",
            ]

    def parse(self, response):
        # The logic in parse_category is correct for search/category pages
        yield from self.parse_category(response)

    def parse_category(self, response):
        products = response.css("li.product-base") or \
                   response.css("div.product-base") or \
                   response.css("div.product-container")
        
        self.logger.info(f"Found {len(products)} products on {response.url}")

        for product in products:
            # Brand + Product Name
            brand = product.css("h3.product-brand::text").get() or ""
            product_name = product.css("h4.product-product::text").get() or ""
            name = f"{brand} {product_name}".strip()
            
            # Image extraction with fallbacks
            image_url = product.css("img.img-responsive::attr(src)").get() or \
                        product.css("picture img::attr(src)").get() or \
                        product.css("img::attr(data-src)").get() or \
                        product.css("img::attr(srcset)").get()

            price = product.css("div.product-price span.product-discountedPrice::text").get() or \
                    product.css("span.product-discountedPrice::text").get() or \
                    product.css("div.product-price::text").get()
            
            url = product.css("a::attr(href)").get()

            if name and price and url:
                full_url = response.urljoin(url)
                product_id = full_url.split("/")[-1].split("?")[0]

                yield ProductItem(
                    product_id=product_id,
                    name=name,
                    price=price,
                    platform="Myntra",
                    url=full_url,
                    date=datetime.utcnow().date(),
                    image_url=image_url
                )

                yield PriceHistoryItem(
                    product_id=product_id,
                    date=datetime.utcnow().date(),
                    price=price,
                    platform="Myntra"
                )
            else:
                self.logger.debug(f"Missing data: name={name}, price={price}, url={url}")

        # Pagination
        next_page = response.css("a.pagination-next::attr(href)").get() or \
                    response.css("li.pagination-next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse_category)

        # Categories
        categories = response.css("div.categories-list a")
        for category in categories:
            category_name = category.css("::text").get()
            category_url = category.attrib.get("href")

            if category_name and category_url:
                yield CategoryItem(
                    category_name=category_name.strip(),
                    category_url=response.urljoin(category_url),
                    parent_category=None,
                    platform="Myntra"
                )

        # Platform info (emit once)
        yield PlatformItem(
            platform_name="Myntra",
            platform_url="https://www.myntra.com",
            country="India"
        )