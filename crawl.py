from pymongo import MongoClient
from spider.spider import FacebookSpider
from spider.settings import (
    DB_NAME,
    FACEBOOK_CREDENTIALS
)


def start_crawl():
    conn = MongoClient('localhost', 27017)

    db = conn[DB_NAME]

    timeline = db['timeline']

    spider = FacebookSpider(timeline)
    spider.login(*FACEBOOK_CREDENTIALS)
    spider.crawl()


if __name__ == '__main__':
    start_crawl()
