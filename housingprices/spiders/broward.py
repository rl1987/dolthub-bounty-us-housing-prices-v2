import scrapy

from scrapy.http import FormRequest

from dateutil.parser import parse as parse_datetime

from datetime import date, datetime, timedelta
import logging

from housingprices.items import SalesItem

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
        item = SalesItem()
        
        item['state'] = 'FL'
        item['property_street_address'] = response.xpath('//tr[./td/span[contains(text(), "Site Address")]]/td[last()]//script/text()').get("").replace("UpdateTitle('", "").replace("')", "")

        units_beds_baths = response.xpath('//tr[./td/span[contains(text(), "Units/Beds/Baths")]]/td[last()]//span/text()').get("").strip()
        units_beds_baths = units_beds_baths.split('/')
        if len(units_beds_baths) == 3:
            item['building_num_units'] = units_beds_baths[0]
            item['building_num_beds'] = units_beds_baths[1]
            item['building_num_baths'] = units_beds_baths[2]
        
        item['building_year_built'] = response.xpath('//a[@href="RecEffNote.asp"]/@onclick').get("").replace("','Menu')", "").split("&Act=")[-1]
        item['source_url'] = response.url

        land_value_by_year = dict()
        building_value_by_year = dict()
        total_value_by_year = dict()

        for row in response.xpath('//span[contains(text(), "Property Assessment Values")]/parent::*/parent::*/parent::*/tr/parent::*/tr'):
            row = row.xpath('./td')
            if len(row) < 4:
                continue

            # Whoever coded this site should fucking die.

            year = row[0].xpath('./span/text()').get()
            if year is None or year == '':
                year = row[0].xpath('./span/span/text()').get()

            if year is None or year == '':
                year = row[0].xpath('./span/font/text()').get()

            if type(year) == str:
                year = year.strip()

            print(year)
            if year is None or len(year) != 4 or year == 'Year':
                continue
            
            year = int(year)

            row = list(map(lambda td: td.xpath('./span/text()').get("").strip(), row))

            land_value = row[1].replace("$", "").replace(",", "")
            building_value = row[2].replace("$", "").replace(",", "")
            total_value = row[3].replace("$", "").replace(",", "")

            land_value_by_year[year] = land_value
            building_value_by_year[year] = building_value
            total_value_by_year[year] = total_value
        
        logging.info(item)
        print(land_value_by_year)
        print(building_value_by_year)
        print(total_value_by_year)
        
        record_urls = response.xpath('//a[contains(@href, "AcclaimWeb")]/@href').getall()

        logging.info(record_urls)

