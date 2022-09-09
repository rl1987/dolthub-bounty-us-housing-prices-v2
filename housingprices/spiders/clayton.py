import scrapy

from scrapy.http import FormRequest

class ClaytonSpider(scrapy.Spider):
    name = 'clayton'
    allowed_domains = ['publicaccess.claytoncountyga.gov']
    start_urls = ['https://publicaccess.claytoncountyga.gov/Search/Disclaimer.aspx?FromUrl=../search/advancedsearch.aspx?mode=sales']

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_disclaimer_page)

    def parse_disclaimer_page(self, response):
        yield FormRequest.from_response(response, formxpath='//form[@name="Form1"]', clickdata={'name':'btAgree'}, callback=self.parse_form_page)

    def parse_form_page(self, response):
        pass
