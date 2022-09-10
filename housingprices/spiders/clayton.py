import scrapy

from scrapy.http import FormRequest

import calendar
from datetime import datetime, date
import logging
from urllib.parse import urljoin

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

    def extract_form(self, response, form_xpath):
        form_data = dict()

        for hidden_input in response.xpath(form_xpath).xpath('.//input'):
            name = hidden_input.attrib.get('name')
            if name is None:
                continue
            value = hidden_input.attrib.get('value')
            if value is None:
                value = ''

            form_data[name] = value

        return form_data

    def make_search_form_request(self, response, start_date, end_date):
        start_date_str = self.stringify_date(start_date)
        end_date_str = self.stringify_date(end_date)

        form_data = self.extract_form(response, '//form[@name="frmMain"]')

        form_data['hdCriteria'] = 'salesdate|{}~{}'.format(start_date_str, end_date_str)
        form_data['ctl01$cal1'] = start_date.isoformat()
        form_data['ctl01$cal1$dateInput'] = start_date_str
        form_data['txtCrit'] = start_date_str
        form_data['ctl01$cal2'] = end_date.isoformat()
        form_data['ctl01$cal2$dateInput'] = end_date_str
        form_data['txtCrit2'] = end_date_str
        form_data['PageNum'] = '1'
        form_data['PageSize'] = '1'
        form_data['hdCriteriaTypes'] = 'N|N|C|C|C|N|C|C|N|D|N|N|C|C|C|N|N'
        form_data['sCriteria'] = '0'

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

        logging.debug(first_row.xpath(".//text()").getall())

        onclick = first_row.attrib.get('onclick')
        rel_url = onclick.replace("javascript:selectSearchRow('", "").replace("')", "")

        form_data = self.extract_form(response, '//form[@name="frmMain"]')
        form_data['hdLink'] = rel_url
        form_data['hdAction'] = 'Link'
        form_data['hdSelectAllChecked'] = 'false'
        form_data['sCriteria'] = '0'
        logging.debug(form_data)

        action = response.xpath('//form[@name="frmMain"]/@action').get()
        form_url = urljoin(response.url, action)

        yield FormRequest(form_url, formdata=form_data, callback=self.parse_property_main_page)

    def parse_property_main_page(self, response):
        parid = response.xpath('//input[@id="hdXPin"]/@value').get()
        property_street_address = response.xpath('//tr[@id="datalet_header_row"]//td[@class="DataletHeaderBottom"]/text()').get()

        partial_item = {
            'state': "GA",
            'property_id': parid,
            'property_street_address': property_street_address,
            'property_county': "CLAYTON",

        }
        
        yield partial_item

        to_from_input_text = response.xpath('//input[@name="DTLNavigator$txtFromTo"]/@value').get()
        idx, total = to_from_input_text.split(" of ")
        idx = int(idx)
        total = int(total)
        
        if idx == total:
            return

        form_data = self.extract_form(response, '//form[@name="frmMain"]')
        del form_data['DTLNavigator$imageNext']
        del form_data['DTLNavigator$imageLast']
        form_data['DTLNavigator$imageNext.x'] = '0' # XXX
        form_data['DTLNavigator$imageNext.y'] = str(idx + 1)
        logging.info(form_data)

        action = response.xpath('//form[@name="frmMain"]/@action').get()
        form_url = urljoin(response.url, action)

        yield FormRequest(form_url, formdata=form_data, callback=self.parse_property_main_page)
