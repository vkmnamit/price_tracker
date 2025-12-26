import pymongo
from itemadapter import ItemAdapter

class PriceScraperPipeline:
    def process_item(self, item, spider):
        return item

class MongoPipeline:
    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        # Map item classes to collection names
        self.collection_mapping = {
            'ProductItem': 'prices',  # Keep 'prices' for products as backend expects
            'PriceHistoryItem': 'price_history',
            'PlatformItem': 'platforms',
            'CategoryItem': 'categories',
            'ReviewItem': 'reviews',
            'SellerItem': 'sellers',
            'StockItem': 'stocks',
            'DiscountItem': 'discounts'
        }

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        data = adapter.asdict()
        item_class = item.__class__.__name__
        collection_name = self.collection_mapping.get(item_class, 'misc')

        # Clean price-related fields
        price_fields = ['price', 'original_price', 'discounted_price', 'shipping_cost']
        for field in price_fields:
            if field in data and data[field] is not None:
                try:
                    if isinstance(data[field], str):
                        # Remove currency symbols, commas, and other non-numeric chars
                        # Keep only digits and the first dot
                        clean_val = "".join(c for c in data[field] if c.isdigit() or c == '.')
                        if clean_val.count('.') > 1:
                            # Handle cases with multiple dots if any
                            parts = clean_val.split('.')
                            clean_val = parts[0] + "." + "".join(parts[1:])
                        data[field] = float(clean_val)
                except (ValueError, TypeError):
                    pass

        # Convert date to string if it's a date object
        date_fields = ['date', 'start_date', 'end_date']
        for field in date_fields:
            if field in data and data[field] is not None and not isinstance(data[field], str):
                data[field] = str(data[field])

        # Save to the mapped collection with upsert logic for certain items
        if item_class == 'ProductItem':
            # Update product if it exists for the same platform
            self.db[collection_name].update_one(
                {'product_id': data['product_id'], 'platform': data['platform']},
                {'$set': data},
                upsert=True
            )
        elif item_class == 'PlatformItem':
            # Update platform info if it exists
            self.db[collection_name].update_one(
                {'platform_name': data['platform_name']},
                {'$set': data},
                upsert=True
            )
        else:
            # Just insert for history, reviews, etc.
            self.db[collection_name].insert_one(data)
            
        return item
