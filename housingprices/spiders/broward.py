import scrapy

from datetime import date, timedelta
import logging
import json

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

            folio_no = result_dict.get("folioNumber")
            
            payload = 'folioNumber: "{}",taxyear: "{}"'.format(folio_no, tax_year)
            payload = '{' + payload + '}'
            logging.debug(payload)

            yield scrapy.Request("https://web.bcpa.net/bcpaclient/search.aspx/getParcelInformationData", headers=self.headers, method="POST", body=payload, callback=self.parse_parcelinfo_api_response)

        if len(results) == PER_PAGE:
            logging.warn("More than PER_PAGE results!")

    def parse_parcelinfo_api_response(self, response):
        json_str = response.text
        json_dict = json.loads(json_str)

        try:
            result_dict = json_dict.get("d")[0]
        except:
            return

        # TODO: parse stuff into item


