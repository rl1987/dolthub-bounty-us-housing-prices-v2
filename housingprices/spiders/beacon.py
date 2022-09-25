import scrapy


class BeaconSpider(scrapy.Spider):
    name = "beacon"
    allowed_domains = ["beacon.schneidercorp.com"]
    start_urls = ["http://beacon.schneidercorp.com/"]

    def parse(self, response):
        pass
