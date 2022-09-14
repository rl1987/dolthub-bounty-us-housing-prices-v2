import scrapy


class AdamsSpider(scrapy.Spider):
    name = 'adams'
    allowed_domains = ['gisapp.adcogov.org']
    start_urls = ['https://gisapp.adcogov.org/PropertySearch/?selectedAccountTypes=Residential']

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_list_page)

    def parse_list_page(self, response):
        for url in response.xpath('//table//td/a/@href').getall():
            yield scrapy.Request(url, callback=self.parse_details_page)

        next_page_link = response.xpath('//li[@class="PagedList-skipToNext"]/a/@href').get()
        if next_page_link is not None:
            yield response.follow(next_page_link, callback=self.parse_list_page)

    def parse_details_page(self, response):
        pass
