import scrapy


class ClaytonSpider(scrapy.Spider):
    name = 'clayton'
    allowed_domains = ['publicaccess.claytoncountyga.gov']
    start_urls = ['https://publicaccess.claytoncountyga.gov/search/advancedsearch.aspx?mode=sales']

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_form_page)

    def parse_form_page(self, response):
        pass
