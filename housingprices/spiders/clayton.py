import scrapy


class ClaytonSpider(scrapy.Spider):
    name = 'clayton'
    allowed_domains = ['publicaccess.claytoncountyga.gov']
    start_urls = ['http://publicaccess.claytoncountyga.gov/']

    def parse(self, response):
        pass
