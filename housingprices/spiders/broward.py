import scrapy


class BrowardSpider(scrapy.Spider):
    name = 'broward'
    allowed_domains = ['web.bcpa.net']
    start_urls = ['http://web.bcpa.net/']

    def parse(self, response):
        pass
