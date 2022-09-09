import scrapy

from scrapy.http import FormRequest

import calendar
from datetime import datetime, date
import logging

class ClaytonSpider(scrapy.Spider):
    name = 'clayton'
    allowed_domains = ['publicaccess.claytoncountyga.gov']
    start_urls = ['https://publicaccess.claytoncountyga.gov/Search/Disclaimer.aspx?FromUrl=../search/advancedsearch.aspx?mode=advanced']
    start_year = 1939

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_disclaimer_page)

    def parse_disclaimer_page(self, response):
        yield FormRequest.from_response(response, formxpath='//form[@name="Form1"]', clickdata={'name':'btAgree'}, callback=self.parse_form_page)

    def stringify_date(self, d):
        return "{:02d}/{:02d}/{:04d}".format(d.month, d.day, d.year)

    def make_search_form_request(self, response, start_date, end_date):
        start_date_str = self.stringify_date(start_date)
        end_date_str = self.stringify_date(end_date)

        form_data = dict()

        for hidden_input in response.xpath('//form[@name="frmMain"]/input'):
            name = hidden_input.attrib.get('name')
            value = hidden_input.attrib.get('value')
            if value is None:
                value = ''

            form_data[name] = value

        form_data['hdCriteria'] = 'salesdate|{}~{}'.format(start_date_str, end_date_str)
        form_data['ctl01$cal1'] = start_date.isoformat()
        form_data['ctl01$cal1$dateInput'] = start_date_str
        form_data['txtCrit'] = start_date_str
        form_data['ctl01$cal2'] = end_date.isoformat()
        form_data['ctl01$cal2$dateInput'] = end_date_str
        form_data['txtCrit2'] = end_date_str

        logging.debug(form_data)

        return FormRequest(response.url, formdata=form_data, callback=self.parse_search_result_list)

    def parse_form_page(self, response):
        for year in range(self.start_year, datetime.today().year + 1):
            for month in range(1, 13):
                days_in_month = calendar.monthrange(year, month)[1]
                
                start_date = date(year=year, month=month, day=1)
                end_date = date(year=year, month=month, day=days_in_month)

                yield self.make_search_form_request(response, start_date, end_date)

    def parse_search_result_list(self, response):
        first_row = response.xpath('//tr[@class="SearchResults"][1]')
        if len(first_row) != 1:
            return

        yield None

