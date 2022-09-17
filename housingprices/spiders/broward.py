import scrapy

from scrapy.http import FormRequest

from dateutil.parser import parse as parse_datetime

from datetime import date, datetime, timedelta
import logging

class BrowardSpider(scrapy.Spider):
    name = 'broward'
    allowed_domains = ['bcpa.net']
    start_urls = ['https://bcpa.net/RecSale.asp']
    stats_filepath = None

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_form_page)

    def parse_form_page(self, response):
        d = date(year=2018, month=1, day=1)

        while d < date.today():
            form_data = {
                'Type': 'RES',
                'SubType': 'ResAll',
                'Months': '',
                'DateMinMonth': str(d.month),
                'DateMinDay': str(d.day),
                'DateMinYear': str(d.year),
                'DateMin': '{}/{}/{}'.format(d.month, d.day, d.year),
                'DateMaxMonth': str(d.month),
                'DateMaxDay': str(d.day),
                'DateMaxYear': str(d.year),
                'DateMax': '{}/{}/{}'.format(d.month, d.day, d.year),
                'AmtMin': '',
                'AmtMax': '',
                'Beds': '',
                'Baths': '',
                'QualSale': 'Y',
                'MinSale': 'N',
                'Location': '',
                'SubLocation': '',
            }

            d += timedelta(days=1)

            logging.debug(form_data)

            yield FormRequest('https://bcpa.net/RecSaleSearch.asp?Sort=Date', formdata=form_data, callback=self.parse_property_list)

    def parse_property_list(self, response):
        for property_link in response.xpath('//a[starts-with(@href, "RecInfo.asp?URL_Folio=")]/@href').getall():
            yield response.follow(property_link, callback=self.parse_property_page)

        next_page_link = response.xpath('//a[contains(text(), "Next 50")]/@href').get()
        if next_page_link is not None:
            yield response.follow(next_page_link, callback=self.parse_property_page)

    def parse_property_page(self, response):
        pass

