import scrapy

from housingprices.items import SalesItem

from dateutil.parser import parse as parse_datetime


class AdamsSpider(scrapy.Spider):
    name = "adams"
    allowed_domains = ["gisapp.adcogov.org"]
    start_urls = [
        "https://gisapp.adcogov.org/PropertySearch/?selectedAccountTypes=Residential"
    ]

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_list_page)

    def parse_list_page(self, response):
        for url in response.xpath("//table//td/a/@href").getall():
            yield scrapy.Request(url, callback=self.parse_details_page)

        next_page_link = response.xpath(
            '//li[@class="PagedList-skipToNext"]/a/@href'
        ).get()
        if next_page_link is not None:
            yield response.follow(next_page_link, callback=self.parse_list_page)

    def parse_details_page(self, response):
        item = SalesItem()

        item["state"] = "CO"
        item["property_street_address"] = " ".join(
            response.xpath(
                '//tr[@id="propertyAddressRow2"]/td[@id="propertyContentCell"]/span/font/text()'
            ).getall()
        ).strip()
        item["property_county"] = "ADAMS"
        item["property_id"] = response.xpath(
            '//span[@class="ParcelIDAndOwnerInformation"]//span[last()]//text()'
        ).get()
        item["property_type"] = "Residential"
        item["building_year_built"] = response.xpath(
            '//tr[.//*[text()="Year Built:"]]/td[last()]//text()'
        ).get()
        item["source_url"] = response.url
        item["building_num_beds"] = response.xpath(
            '//tr[.//*[text()="Number of Bedrooms:"]]/td[last()]//text()'
        ).get()
        item["building_num_baths"] = (
            response.xpath('//tr[.//*[text()="Number of Baths:"]]/td[last()]//text()')
            .get("")
            .split(".")[0]
        )
        item["building_area_sqft"] = response.xpath(
            '//tr[.//*[text()="Built As SQ Ft:"]]/td[last()]//text()'
        ).get()
        # XXX: is this right?
        # There could be multiple buildings:
        # https://gisapp.adcogov.org/QuickSearch/doreport.aspx?pid=0156309200002
        item["building_assessed_value"] = (
            response.xpath(
                '//tr[.//*[text()="Improvements Subtotal:"]]/td[last()]//text()'
            )
            .get("")
            .replace("$", "")
            .replace(",", "")
        )
        item["building_appraised_value"] = (
            response.xpath('//tr[.//*[text()="Improvements Subtotal:"]]/td[2]//text()')
            .get("")
            .replace("$", "")
            .replace(",", "")
            .split(".")[0]
        )
        if "." in item["building_assessed_value"]:
            item["building_assessed_value"] = round(
                float(item["building_assessed_value"])
            )

        land_data_row = response.xpath(
            '//span[@class="AssessorValuationSummary"]/div[1]/table[.//*[text()="Land Subtotal:"]]/tr[2]/td//text()'
        ).getall()
        if len(land_data_row) == 9:
            item["land_type"] = land_data_row[1]
            if land_data_row[2] == "Acres":
                try:
                    item["land_area_acres"] = round(float(land_data_row[3]))
                except:
                    pass

            item["land_assessed_value"] = (
                land_data_row[-1].replace("$", "").replace(",", "").split(".")[0]
            )
            item["land_appraised_value"] = (
                land_data_row[-2].replace("$", "").replace(",", "").split(".")[0]
            )

        header = None

        for row in response.xpath('//span[@class="SalesSection"]//table/tr'):
            row = row.xpath("./td")
            row = list(map(lambda td: td.xpath(".//text()").get(""), row))

            if header is None:
                header = row
                continue

            row = dict(zip(header, row))

            item["sale_datetime"] = (
                parse_datetime(row.get("Sale Date")).isoformat().replace("T", " ")
            )
            item["sale_price"] = (
                row.get("Sale Price", "")
                .replace("$", "")
                .replace(",", "")
                .split(".")[0]
            )
            item["transfer_deed_type"] = row.get("Deed Type")
            item["book"] = row.get("Book")
            item["page"] = row.get("Page")
            item["seller_1_name"] = row.get("Grantor")
            item["buyer_1_name"] = row.get("Grantee")
            if row.get("Doc. Date") is not None and row.get("Doc. Date") != "":
                item["deed_date"] = (
                    parse_datetime(row.get("Doc. Date")).isoformat().split("T")[0]
                )

            yield item
