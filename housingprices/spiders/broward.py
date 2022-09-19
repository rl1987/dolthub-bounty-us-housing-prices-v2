import scrapy

from datetime import date, timedelta
import logging
import json

from housingprices.items import SalesItem

PER_PAGE = 100

class BrowardSpider(scrapy.Spider):
    name = 'broward'
    allowed_domains = ['web.bcpa.net']
    stats_filepath = None

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json; charset=UTF-8',
        'Origin': 'https://web.bcpa.net',
        'Pragma': 'no-cache',
        'Referer': 'https://web.bcpa.net/bcpaclient/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
    }

    def start_requests(self):
        url = "https://web.bcpa.net/bcpaclient/searchallsales.aspx/getSaleTypeResult"
        
        d = date(year=2016, month=1, day=1)

        while d < date.today():
            date_str = "{}/{}/{}".format(d.month, d.day, d.year)

            payload = "type: \"RES\",subtype: \"RESALL\",datemin: \"{}\",datemax: \"{}\",amountmin: \"\",amountmax: \"\",beds: \"0\",baths: \"0\",qualified: \"Y\",minsale: \"Y\",location: \"\",order: \"FOLIO\",pagenum: \"1\",pagecount: \"100\"".format(date_str, date_str)

            payload = '{' + payload + '}'

            logging.debug(payload)

            yield scrapy.Request(url, method="POST", headers=self.headers, body=payload, callback=self.parse_search_api_response)

            d += timedelta(days=1)

    def parse_search_api_response(self, response):
        json_str = response.text
        json_dict = json.loads(json_str)

        results = json_dict.get("d", [])

        for result_dict in results:
            sale_date_str = result_dict.get("saleDate")
            if sale_date_str is None:
                continue

            tax_year = sale_date_str.split("/")[-1]
            tax_year = int(tax_year)

            folio_no = result_dict.get("folioNumber")
            
            payload = 'folioNumber: "{}",taxyear: "{}"'.format(folio_no, tax_year)
            payload = '{' + payload + '}'
            logging.debug(payload)

            yield scrapy.Request("https://web.bcpa.net/bcpaclient/search.aspx/getParcelInformationData", headers=self.headers, method="POST", body=payload, callback=self.parse_parcelinfo_api_response, meta={"tax_year": tax_year})

        if len(results) == PER_PAGE:
            old_payload = response.request.body
            old_payload = str(old_payload)
            pagenum_at = old_payload.index("pagenum: \"") + len("pagenum: \"")
            pagenum = old_payload[pagenum_at:].split("\"")[0]
            pagenum = int(pagenum)
            pagenum += 1
            payload = old_payload[:pagenum_at] + str(pagenum) + '", pagecount: "100"}'
            logging.debug(payload)

            url = "https://web.bcpa.net/bcpaclient/searchallsales.aspx/getSaleTypeResult"
            yield scrapy.Request(url, method="POST", headers=self.headers, body=payload, callback=self.parse_search_api_response)

    def parse_date_str(self, date_str):
        components = date_str.split("/")
        if len(components) != 3:
            return None

        return date(year=int(components[2]), month=int(components[0]), day=int(components[1]))

    def parse_parcelinfo_api_response(self, response):
        tax_year = response.meta.get("tax_year")

        json_str = response.text
        json_dict = json.loads(json_str)

        try:
            json_dict = json_dict.get("d")[0]
        except:
            return

        item = SalesItem()
        item['state'] = 'FL'
        item['property_zip5'] = json_dict.get('situsZipCode')
        item['property_street_address'] = json_dict.get('situsAddress1')
        item['property_city'] = json_dict.get('situsCity')
        item['property_county'] = 'BROWARD'
        item['property_id'] = json_dict.get("folioNumber")
        item['building_num_units'] = json_dict.get("units")
        item['building_year_built'] = json_dict.get("actualAge")
        item['source_url'] = 'https://web.bcpa.net/bcpaclient/#/Sales-Search'
        item['building_num_beds'] = json_dict.get('beds')
        item['building_num_baths'] = json_dict.get('baths')
        item['building_area_sqft'] = json_dict.get("bldgSqFT")
        
        i = 1

        while True:
            type_field_name = "landCalcType" + str(i)
            if not type_field_name in json_dict:
                break

            type_field_value = json_dict.get(type_field_name)
            if type_field_value == "Square Foot":
                fact_field_name = "landCalcFact" + str(i)
                fact_field_value = json_dict.get(fact_field_name)
                if type(fact_field_value) == str:
                    item['land_area_sqft'] = fact_field_value.replace(",", "").replace(" SqFt", "")
            i += 1

        item['land_type'] = json_dict.get("landCalcZoning") # XXX: is this right?
        if json_dict.get("sohValue") is not None:
            item['total_assessed_value'] = json_dict.get("sohValue").replace("$", "").replace(",", "")

        if json_dict.get("landValue") is not None:
            item['land_appraised_value'] = json_dict.get("landValue").replace("$", "").replace(",", "")
        if json_dict.get("bldgValue") is not None:
            item['building_appraised_value'] = json_dict.get("bldgValue").replace("$", "").replace(",", "")
        if json_dict.get("justValue") is not None:
            item['total_appraised_value'] = json_dict.get("justValue").replace("$", "").replace(",", "")

        i = 1
    
        while True:
            sale_date_field_name = "saleDate" + str(i)
            if not sale_date_field_name in json_dict:
                break

            sale_date_str = json_dict.get(sale_date_field_name)
            sale_date = self.parse_date_str(sale_date_str)
            if sale_date is None or sale_date.year != tax_year:
                i += 1
                continue
    
            item['sale_datetime'] = sale_date.isoformat().replace("T", " ")
            sale_price_field_name = "stampAmount" + str(i)
            item['sale_price'] = json_dict.get(sale_price_field_name)
            if type(item['sale_price']) == str:
                item['sale_price'] = item['sale_price'].replace("$", "").replace(",", "")

            book_page_field_name = "bookAndPageOrCin" + str(i)
            book_page = json_dict.get(book_page_field_name)
            if book_page is not None and " / " in book_page:
                book, page = book_page.split(" / ")
                item['book'] = book
                item['page'] = page
            else:
                item['sale_id'] = book_page
            
            deed_type_field_name = "deedType" + str(i)
            item['transfer_deed_type'] = json_dict.get(deed_type_field_name)

            i += 1

            yield item

