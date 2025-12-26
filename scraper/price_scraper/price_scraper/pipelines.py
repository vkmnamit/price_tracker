from pymongo import MongoClient

class MongoPipeline:
    def open_spider(self, spider):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client["price_tracker"]

    def process_item(self, item, spider):
        self.db.prices.insert_one(dict(item))
        return item
    def close_spider(self, spider):
        self.client.close()
        