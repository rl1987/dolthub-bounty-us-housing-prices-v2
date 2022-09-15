import scrapy


class BrowardSpider(scrapy.Spider):
    name = 'broward'
    allowed_domains = ['broward.org']
    start_urls = ['http://broward.org/']

    def parse(self, response):
        pass
