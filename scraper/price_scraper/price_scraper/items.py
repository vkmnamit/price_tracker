import scrapy

class ProductItem(scrapy.Item):
    product_id = scrapy.Field()
    name = scrapy.Field()
    price = scrapy.Field()
    platform = scrapy.Field()
    url = scrapy.Field()
    date = scrapy.Field()

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
class SpecificationItem(scrapy.Item):
    product_id = scrapy.Field()
    specifications = scrapy.Field()  # This can be a dictionary of spec name and value
    platform = scrapy.Field()
    date = scrapy.Field()


class SellerRatingItem(scrapy.Item):
    seller_id = scrapy.Field()
    rating = scrapy.Field()
    number_of_reviews = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()


class ShippingItem(scrapy.Item):
    product_id = scrapy.Field()
    shipping_cost = scrapy.Field()
    delivery_time = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class WarrantyItem(scrapy.Item):
    product_id = scrapy.Field()
    warranty_period = scrapy.Field()
    warranty_details = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()


class PromotionItem(scrapy.Item):
    product_id = scrapy.Field()
    promotion_details = scrapy.Field()
    start_date = scrapy.Field()
    end_date = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class TagItem(scrapy.Item):
    product_id = scrapy.Field()
    tag = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class RelatedProductItem(scrapy.Item):
    product_id = scrapy.Field()
    related_product_id = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class VideoItem(scrapy.Item):   
    product_id = scrapy.Field()
    video_url = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class ColorVariantItem(scrapy.Item):
    product_id = scrapy.Field()
    color = scrapy.Field()
    variant_url = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class SizeVariantItem(scrapy.Item):
    product_id = scrapy.Field()
    size = scrapy.Field()
    variant_url = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()

class MaterialItem(scrapy.Item):
    product_id = scrapy.Field()
    material = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()
    
class FeatureItem(scrapy.Item):
    product_id = scrapy.Field()
    feature = scrapy.Field()
    platform = scrapy.Field()
    date = scrapy.Field()