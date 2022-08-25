#!/usr/bin/python3

import csv
import requests
from urllib.parse import urljoin

from lxml import html

FIELDNAMES = ["filename", "url"]


def scrape_xlsx_urls(page_url, csv_file_path):
    out_f = open(csv_file_path, "w", encoding="utf-8")

    csv_writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES, lineterminator="\n")
    csv_writer.writeheader()

    resp = requests.get(page_url)
    print(resp.url)

    tree = html.fromstring(resp.text)

    for xlsx_link in tree.xpath('//a[contains(@href, ".xls")]/@href'):
        xlsx_url = urljoin(resp.url, xlsx_link)
        filename = xlsx_link.split("/")[-1]

        row = {"filename": filename, "url": xlsx_url}
        print(row)

        csv_writer.writerow(row)

    out_f.close()


def main():
    scrape_xlsx_urls(
        "https://www1.nyc.gov/site/finance/taxes/property-rolling-sales-data.page",
        "rolling_xlsx_urls.csv",
    )
    scrape_xlsx_urls(
        "https://www1.nyc.gov/site/finance/taxes/property-annualized-sales-update.page",
        "yearly_xlsx_urls.csv",
    )


if __name__ == "__main__":
    main()
