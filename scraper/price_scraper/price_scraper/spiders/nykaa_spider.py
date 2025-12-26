from scrapy import Spider
from datetime import datetime
from price_scraper.items import (
    ProductItem, PriceHistoryItem, PlatformItem, CategoryItem,
    ReviewItem, SellerItem, StockItem, DiscountItem
)       
class NykaaSpider(Spider):
    name = "nykaa_spider"
    allowed_domains = ["nykaa.com", "nykaafashion.com"]
    start_urls = [
        "https://www.nykaa.com/makeup/c/12",
        "https://www.nykaa.com/skin/c/8377",
        "https://www.nykaafashion.com/women/c/6513",
        "https://www.nykaafashion.com/men/c/10000",
        "https://www.nykaafashion.com/electronics/c/10549",
        "https://www.nykaafashion.com/jewelry/c/11187",
        "https://www.nykaafashion.com/health-beauty/c/10549",
        "https://www.nykaafashion.com/health-beauty/c/10549",
    ]

    def parse(self, response):
        # Find all category links from the homepage
        category_links = response.css('a[href*="/category/"]::attr(href)').getall()
        seen = set()
        for link in category_links:
            full_link = response.urljoin(link)
            if full_link not in seen:
                seen.add(full_link)
                yield response.follow(full_link, self.parse_category)

    def parse_category(self, response):
        products = response.css("div.product-listing div.product-item") or \
                   response.css("div.productSummary") or \
                   response.css("div.css-1d0p6b")
        
        self.logger.info(f"Found {len(products)} products on {response.url}")

        for product in products:
            name = product.css("h2.product-name::text").get() or \
                   product.css("div.css-xrzm88::text").get() or \
                   product.css("div.product-title::text").get()
            
            price = product.css("span.product-price::text").get() or \
                    product.css("span.css-117yc9e::text").get() or \
                    product.css("div.price-info::text").get()
            
            url = product.css("a.product-link::attr(href)").get() or \
                  product.css("a.css-ql46ps::attr(href)").get() or \
                  product.css("a::attr(href)").get()

            if name and price and url:
                full_url = response.urljoin(url)
                product_id = full_url.split("/")[-1].split("?")[0]

                yield ProductItem(
                    product_id=product_id,
                    name=name.strip(),
                    price=price,
                    platform="Nykaa",
                    url=full_url,
                    date=datetime.utcnow().date()
                )

                yield PriceHistoryItem(
                    product_id=product_id,
                    date=datetime.utcnow().date(),
                    price=price,
                    platform="Nykaa"
                )
            else:
                self.logger.debug(f"Missing data: name={name}, price={price}, url={url}")

        # Pagination
        next_page = response.css("a.pagination-next::attr(href)").get() or \
                    response.css("div.pagination-btn-next a::attr(href)").get()
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
                    platform="Nykaa"
                )

        # Platform info (emit once)
        yield PlatformItem(
            platform_name="Nykaa",
            platform_url="https://www.nykaa.com",
            country="India"
        )
