from scrapy import Spider
from datetime import datetime
from price_scraper.items import (
    ProductItem, PriceHistoryItem, PlatformItem, CategoryItem
)

class FlipkartSpider(Spider):
    name = "flipkart_spider"
    allowed_domains = ["flipkart.com"]
    def __init__(self, query=None, *args, **kwargs):
        super(FlipkartSpider, self).__init__(*args, **kwargs)
        if query:
            self.start_urls = [f"https://www.flipkart.com/search?q={query}"]
        else:
            self.start_urls = [
                "https://www.flipkart.com/search?q=smartwatches",
                "https://www.flipkart.com/search?q=mens+watches",
                "https://www.flipkart.com/search?q=womens+watches",
                "https://www.flipkart.com/search?q=sneakers",
                "https://www.flipkart.com/search?q=running+shoes",
                "https://www.flipkart.com/search?q=monitors",
                "https://www.flipkart.com/search?q=speakers",
                "https://www.flipkart.com/search?q=tablets",
                "https://www.flipkart.com/search?q=cameras",
                "https://www.flipkart.com/search?q=smartphones",
                "https://www.flipkart.com/search?q=smart+tv",   
                "https://www.flipkart.com/search?q=smart+refrigerator",
            ]

    def parse(self, response):
        # Follow search links
        category_links = response.css('a[href*="/search?sid="]::attr(href)').getall()
        for link in category_links:
            yield response.follow(link, self.parse_category)
        
        # Also parse current page if it's a category page
        yield from self.parse_category(response)

    def parse_category(self, response):
        products = response.css("div._1AtVbE div._13oc-S") or \
                   response.css("div.slp-list-view") or \
                   response.css("div._1AtVbE") or \
                   response.css("a.k7wcnx") or \
                   response.css("div.cPHDOP") or \
                   response.css("div._75_9Y") or \
                   response.css("div.CGtC98") or \
                   response.css("div._4dd8f5")

        self.logger.info(f"Found {len(products)} products on {response.url}")

        for product in products:
            # Name fallbacks
            name = product.css("div._4rR01T::text").get() or \
                   product.css("div.KzDlHZ::text").get() or \
                   product.css("div.RG5Slk::text").get() or \
                   product.css("a.IRpwCQ::text").get() or \
                   product.css("a.s1Q9rs::text").get() or \
                   product.css("div._2Wk9S::text").get() or \
                   product.css("div.Y_uN9p::text").get() or \
                   product.css("div.w89uY_::text").get() or \
                   product.css("div._3wU53n::text").get()
            
            # Image extraction with fallbacks for lazy loading
            image_url = product.css("img::attr(src)").get() or \
                        product.css("img::attr(data-src)").get() or \
                        product.css("img._396cs4::attr(src)").get() or \
                        product.css("img.V_P96w::attr(src)").get() or \
                        product.css("img._2puESu::attr(src)").get()

            # Price fallbacks
            price = product.css("div._30jeq3::text").get() or \
                    product.css("div.Nx9bqj::text").get() or \
                    product.css("div.hZ3P6w::text").get() or \
                    product.css("div._3I9_wc::text").get()
            
            original_price = product.css("div._3I9_wc._27Uc_P::text").get() or \
                             product.css("div.y_T96m::text").get()
            
            discount = product.css("div._3Ay6Bw span::text").get() or \
                       product.css("div.Uk_O9r span::text").get()
            
            # URL fallbacks
            url = product.css("a._1fQZEK::attr(href)").get() or \
                  product.css("a.IRpwCQ::attr(href)").get() or \
                  product.css("a.Vp_obn::attr(href)").get() or \
                  product.css("a.s1Q9rs::attr(href)").get() or \
                  product.css("a.rPDeY::attr(href)").get()
            
            if not url and product.root.tag == 'a':
                url = product.attrib.get('href')

            if name and price and url:
                full_url = response.urljoin(url)
                product_id = product.attrib.get('data-id')
                if not product_id:
                    product_id = full_url.split("/")[-1].split("?")[0]

                clean_price = price.replace("₹", "").replace(",", "").strip()

                yield ProductItem(
                    product_id=product_id,
                    name=name.strip(),
                    price=clean_price,
                    platform="Flipkart",
                    url=full_url,
                    date=datetime.utcnow().date(),
                    image_url=image_url,
                    original_price=original_price,
                    discount=discount
                )

                yield PriceHistoryItem(
                    product_id=product_id,
                    date=datetime.utcnow().date(),
                    price=clean_price,
                    platform="Flipkart"
                )
            else:
                self.logger.debug(f"Missing data: name={name}, price={price}, url={url}")

        # Pagination fallbacks
        next_page = response.css("a._1LKTO3::attr(href)").get() or \
                    response.css("nav a:contains('Next')::attr(href)").get() or \
                    response.css("a._9Q_9al:contains('Next')::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

        # Categories
        categories = response.css("div._1kidPb a")
        for category in categories:
            category_name = category.css("::text").get()
            category_url = category.attrib.get("href")

            if category_name and category_url:
                yield CategoryItem(
                    category_name=category_name.strip(),
                    category_url=response.urljoin(category_url),
                    parent_category=None,
                    platform="Flipkart"
                )

        # Platform info (emit once)
        yield PlatformItem(
            platform_name="Flipkart",
            platform_url="https://www.flipkart.com",
            country="India"
        )
            