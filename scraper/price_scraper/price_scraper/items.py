import scrapy

class ProductItem(scrapy.Item):
    product_id = scrapy.Field()
    name = scrapy.Field()
    price = scrapy.Field()
    platform = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()
    image_url = scrapy.Field()
    description = scrapy.Field()
    original_price = scrapy.Field()
    discount = scrapy.Field()

class PriceHistoryItem(scrapy.Item):
    product_id = scrapy.Field()
    date = scrapy.Field()
    price = scrapy.Field()
    platform = scrapy.Field()

class PlatformItem(scrapy.Item):
    platform_name = scrapy.Field()
    platform_url = scrapy.Field()
    country = scrapy.Field()

class CategoryItem(scrapy.Item):
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    parent_category = scrapy.Field()
    platform = scrapy.Field()

class ReviewItem(scrapy.Item):
    product_id = scrapy.Field()
    review_id = scrapy.Field()
    rating = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    platform = scrapy.Field()

class SellerItem(scrapy.Item):
    seller_id = scrapy.Field()
    seller_name = scrapy.Field()
    seller_rating = scrapy.Field()
    platform = scrapy.Field()
    seller_url = scrapy.Field()


class StockItem(scrapy.Item):
    product_id = scrapy.Field()
    availability = scrapy.Field()
    stock_quantity = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()


class DiscountItem(scrapy.Item):
    product_id = scrapy.Field()
    original_price = scrapy.Field()
    discounted_price = scrapy.Field()
    discount_percentage = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()
class ImageItem(scrapy.Item):
    product_id = scrapy.Field()
    image_url = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()