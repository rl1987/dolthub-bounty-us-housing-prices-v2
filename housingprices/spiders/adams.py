import scrapy


class AdamsSpider(scrapy.Spider):
    name = 'adams'
    allowed_domains = ['gisapp.adcogov.org']
    start_urls = ['http://gisapp.adcogov.org/']

    def parse(self, response):
        pass
