import scrapy

from scrapy.http import FormRequest
from dateutil.parser import parse as parse_datetime

import calendar
from datetime import datetime, date
import logging
from urllib.parse import urljoin

from housingprices.items import SalesItem


class WashingtonSpider(scrapy.Spider):
    name = "washington"
    allowed_domains = ["tyler.washcopa.org"]
    start_urls = [
        "http://tyler.washcopa.org/pt/Search/Disclaimer.aspx?FromUrl=../search/advancedsearch.aspx?mode=advanced",
        "http://tyler.washcopa.org/pt/search/advancedsearch.aspx?mode=advanced",
    ]
    start_year = 1900
    state = "PA"
    county = "WASHINGTON"
    shards = []
    stats_filepath = None

    def __init__(self, year=None, month=None, stats_filepath=None):
        super().__init__()

        self.stats_filepath = stats_filepath

        if year is not None and month is not None:
            year = int(year)
            month = int(month)
            self.shards = [(year, month)]
            return

        for year in range(self.start_year, datetime.today().year + 1):
            for month in range(1, 13):
                shard = (year, month)
                self.shards.append(shard)

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_disclaimer_page)

    def parse_disclaimer_page(self, response):
        yield FormRequest.from_response(
            response,
            formxpath='//form[@name="Form1"]',
            clickdata={"name": "btAgree"},
            callback=self.parse_form_page,
        )

    def stringify_date(self, d):
        return "{:02d}/{:02d}/{:04d}".format(d.month, d.day, d.year)

    def extract_form(self, response, form_xpath):
        form_data = dict()

        for hidden_input in response.xpath(form_xpath).xpath(".//input"):
            name = hidden_input.attrib.get("name")
            if name is None:
                continue
            value = hidden_input.attrib.get("value")
            if value is None:
                value = ""

            form_data[name] = value

        return form_data

    def make_search_form_request(self, response, start_date, end_date):
        start_date_str = self.stringify_date(start_date)
        end_date_str = self.stringify_date(end_date)

        form_data = self.extract_form(response, '//form[@name="frmMain"]')

        form_data["hdCriteria"] = "salesdate|{}~{}".format(start_date_str, end_date_str)
        form_data["ctl01$cal1"] = start_date.isoformat()
        form_data["ctl01$cal1$dateInput"] = start_date_str
        form_data["txtCrit"] = start_date_str
        form_data["ctl01$cal2"] = end_date.isoformat()
        form_data["ctl01$cal2$dateInput"] = end_date_str
        form_data["txtCrit2"] = end_date_str
        form_data["PageNum"] = "1"
        form_data["PageSize"] = "15"
        form_data["hdCriteriaTypes"] = "C|N|D|N|C|N"
        form_data["sCriteria"] = "0"
        form_data["hdSearchType"] = "AdvSearch"

        logging.debug(form_data)

        return FormRequest(
            response.url,
            formdata=form_data,
            callback=self.parse_search_result_list,
            dont_filter=True,
        )

    def parse_form_page(self, response):
        if len(self.shards) == 0:
            yield None
            return

        year, month = self.shards.pop()
        logging.info("Year: {}, month: {}".format(year, month))

        days_in_month = calendar.monthrange(year, month)[1]

        start_date = date(year=year, month=month, day=1)
        end_date = date(year=year, month=month, day=days_in_month)

        yield self.make_search_form_request(response, start_date, end_date)

    def parse_search_result_list(self, response):
        first_row = response.xpath('//tr[@class="SearchResults"][1]')
        if len(first_row) != 1:
            yield scrapy.Request(
                self.start_urls[-1], callback=self.parse_form_page, dont_filter=True
            )
            return

        logging.debug(first_row.xpath(".//text()").getall())

        onclick = first_row.attrib.get("onclick")
        rel_url = onclick.replace("javascript:selectSearchRow('", "").replace("')", "")

        form_data = self.extract_form(response, '//form[@name="frmMain"]')
        form_data["hdLink"] = rel_url
        form_data["hdAction"] = "Link"
        form_data["hdSelectAllChecked"] = "false"
        form_data["sCriteria"] = "0"
        logging.debug(form_data)

        action = response.xpath('//form[@name="frmMain"]/@action').get()
        form_url = urljoin(response.url, action)

        yield FormRequest(
            form_url,
            formdata=form_data,
            callback=self.parse_property_main_page,
            dont_filter=True,
        )

    def parse_property_main_page(self, response):
        parid = response.xpath('//input[@id="hdXPin"]/@value').get()

        item = SalesItem()
        item["state"] = self.state
        item["property_id"] = parid
        item["property_street_address"] = (
            response.xpath(
                '//tr[./td[text()="Property Address"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["property_street_address"] = " ".join(
            item["property_street_address"].split()
        )  # https://stackoverflow.com/a/1546251
        item["property_county"] = self.county
        item["property_city"] = (
            response.xpath(
                '//tr[./td[text()="Property City/State"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["property_zip5"] = (
            response.xpath(
                '//tr[./td[text()="Property Zip Code"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["property_type"] = response.xpath(
            '//tr[./td[text()="Class"]]/td[@class="DataletData"]/text()'
        ).get()

        main_building_link = response.xpath(
            '//a[./span[text()="Main Building(s)"]]/@href'
        ).get()
        yield response.follow(
            main_building_link,
            meta={"item": item},
            callback=self.parse_property_main_building_page,
            dont_filter=True,
        )

    def parse_property_main_building_page(self, response):
        item = response.meta.get("item")

        parid = response.xpath('//input[@id="hdXPin"]/@value').get()
        assert parid == item["property_id"]

        item["building_year_built"] = response.xpath(
            '//tr[./td[text()="Year Built"]]/td[@class="DataletData"]/text()'
        ).get()
        item["building_num_beds"] = response.xpath(
            '//tr[./td[text()="Bedrooms"]]/td[@class="DataletData"]/text()'
        ).get()
        item["building_num_baths"] = response.xpath(
            '//tr[./td[text()="Full Baths"]]/td[@class="DataletData"]/text()'
        ).get()
        if item["building_num_baths"] is not None:
            item["building_num_baths"] = float(item["building_num_baths"])

            half_baths = response.xpath(
                '//tr[./td[text()="Half Baths"]]/td[@class="DataletData"]/text()'
            ).get()
            if half_baths is not None:
                half_baths = float(half_baths)
                item["building_num_baths"] += half_baths / 2
        item["building_area_sqft"] = (
            response.xpath(
                '//tr[./td[text()="Total Area"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
            .replace(",", "")
        )

        sales_link = response.xpath(
            '//a[./span[text()="Assessment/Sales"]]/@href'
        ).get()
        yield response.follow(
            sales_link,
            meta={"item": item},
            callback=self.parse_property_sales_page,
            dont_filter=True,
        )

    def parse_property_sales_page(self, response):
        item = response.meta.get("item")

        sale_date_str = response.xpath(
            '//tr[./td[text()="Date"]]/td[@class="DataletData"]/text()'
        ).get()
        if sale_date_str is None:
            return

        sale_date = parse_datetime(sale_date_str)
        sale_date_str = sale_date.isoformat().replace("T", " ")

        item["sale_datetime"] = sale_date_str
        item["sale_price"] = (
            response.xpath('//tr[./td[text()="Price"]]/td[@class="DataletData"]/text()')
            .get("")
            .replace("$", "")
            .replace(",", "")
            .split(".")[0]
        )
        item["seller_1_name"] = (
            response.xpath(
                '//tr[./td[text()="Grantor"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["buyer_1_name"] = (
            response.xpath(
                '//tr[./td[text()="Grantee"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["book"] = (
            response.xpath(
                '//tr[./td[text()="Deed Book"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["page"] = (
            response.xpath(
                '//tr[./td[text()="Deed Page"]]/td[@class="DataletData"]/text()'
            )
            .get("")
            .replace("\xa0", "")
        )
        item["source_url"] = self.start_urls[-1]

        item["land_assessed_value"] = None
        item["building_assessed_value"] = None
        item["total_assessed_value"] = None

        assessment_year = response.xpath(
            '//tr[./td[text()="Assessment Year"]]/td[@class="DataletData"]/text()'
        ).get()
        if assessment_year is not None:
            assessment_year = int(assessment_year)
            if assessment_year == sale_date.year:
                item["land_assessed_value"] = (
                    response.xpath(
                        '//tr[./td[text()="Land Value"]]/td[@class="DataletData"]/text()'
                    )
                    .get("")
                    .replace(",", "")
                )
                item["building_assessed_value"] = (
                    response.xpath(
                        '//tr[./td[text()="Building Value"]]/td[@class="DataletData"]/text()'
                    )
                    .get("")
                    .replace(",", "")
                )
                item["total_assessed_value"] = (
                    response.xpath(
                        '//tr[./td[text()="Total Value"]]/td[@class="DataletData"]/text()'
                    )
                    .get("")
                    .replace(",", "")
                )

        yield item

        next_sale_link = response.xpath(
            '//a[./i[@class="icon-angle-right "]]/@href'
        ).get()
        if next_sale_link is not None:
            yield response.follow(
                next_sale_link,
                callback=self.parse_property_sales_page,
                dont_filter=True,
                meta={"item": item},
            )
            return

        to_from_input_text = response.xpath(
            '//input[@name="DTLNavigator$txtFromTo"]/@value'
        ).get()
        idx, total = to_from_input_text.split(" of ")
        idx = int(idx)
        total = int(total)

        if idx == total:
            yield scrapy.Request(
                self.start_urls[-1],
                callback=self.parse_form_page,
                dont_filter=True,
                meta={"item": item},
            )
            return

        form_data = self.extract_form(response, '//form[@name="frmMain"]')
        del form_data["DTLNavigator$imageNext"]
        del form_data["DTLNavigator$imageLast"]
        form_data["DTLNavigator$imageNext.x"] = "0"  # XXX
        form_data["DTLNavigator$imageNext.y"] = str(idx + 1)
        form_data["hdMode"] = "PROFILEALL"
        logging.info(form_data)

        action = response.xpath('//form[@name="frmMain"]/@action').get()
        form_url = urljoin(response.url, action).replace(
            "mode=sales", "mode=profileall"
        )

        yield FormRequest(
            form_url,
            formdata=form_data,
            callback=self.parse_property_main_page,
            dont_filter=True,
        )
