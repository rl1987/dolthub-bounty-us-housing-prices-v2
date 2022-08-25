#!/usr/bin/python3

import sys
import os
import csv
from pprint import pprint

import openpyxl

FIELDNAMES = [
    "state",
    "property_zip5",
    "property_street_address",
    "property_city",
    "property_county",
    "property_id",
    "sale_datetime",
    "property_type",
    "sale_price",
    "seller_1_name",
    "buyer_1_name",
    "building_num_units",
    "building_year_built",
    "source_url",
    "book",
    "page",
    "transfer_deed_type",
    "property_township",
    "property_lat",
    "property_lon",
    "sale_id",
    "deed_date",
    "building_num_stories",
    "building_num_beds",
    "building_num_baths",
    "building_area_sqft",
    "building_assessed_value",
    "building_assessed_date",
    "land_area_acres",
    "land_area_sqft",
    "land_assessed_value",
    "seller_2_name",
    "buyer_2_name",
    "land_assessed_date",
    "seller_1_state",
    "seller_2_state",
    "buyer_1_state",
    "buyer_2_state",
]


def wrangle_data(xlsx_filepath, xlsx_url, csv_writer):
    wb = openpyxl.load_workbook(xlsx_filepath)
    ws = wb.active

    xls_fieldnames = None

    for row in ws:
        row = list(map(lambda cell: cell.value, row))
        if len(row) == 0:
            continue

        if row[0] == "BOROUGH":
            xls_fieldnames = row

            if "NUMBER OF SALES" in xls_fieldnames:
                return

            continue

        if xls_fieldnames is None:
            continue

        row = row[: len(xls_fieldnames)]

        xls_row = dict(zip(xls_fieldnames, row))

        pprint(xls_row)

        # https://en.wikipedia.org/wiki/List_of_counties_in_New_York#Five_boroughs_of_New_York_City
        county = "NEW YORK"
        if "bronx" in xlsx_filepath:
            county = "BRONX"
        elif "brooklyn" in xlsx_filepath:
            county = "KINGS"
        elif "staten" in xlsx_filepath:
            county = "RICHMOND"
        elif "queens" in xlsx_filepath:
            county = "QUEENS"

        out_row = {
            "state": "NY",
            "property_zip5": xls_row.get("ZIP CODE"),
            "property_street_address": xls_row.get("ADDRESS"),
            "property_city": "NEW YORK",
            "property_county": county,
            "property_id": None,
            "sale_datetime": xls_row.get("SALE DATE").isoformat(),
            "property_type": xls_row.get("BUILDING CLASS CATEGORY"),
            "sale_price": str(xls_row.get("SALE PRICE", ""))
            .replace("$", "")
            .replace("US", ""),
            "seller_1_name": None,
            "buyer_1_name": None,
            "building_num_units": xls_row.get("TOTAL UNITS"),
            "building_year_built": xls_row.get("YEAR BUILT"),
            "source_url": xlsx_url,
            "book": None,
            "page": None,
            "transfer_deed_type": None,
            "property_township": None,
            "property_lat": None,
            "property_lon": None,
            "sale_id": None,
            "deed_date": None,
            "building_num_stories": None,
            "building_num_beds": None,
            "building_num_baths": None,
            "building_area_sqft": None,  # XXX
            "building_assessed_value": None,
            "building_assessed_date": None,
            "land_area_acres": None,
            "land_area_sqft": xls_row.get("LAND SQUARE FEET"),
            "land_assessed_value": None,
            "seller_2_name": None,
            "buyer_2_name": None,
            "land_assessed_date": None,
            "seller_1_state": None,
            "seller_2_state": None,
            "buyer_1_state": None,
            "buyer_2_state": None,
        }

        pprint(out_row)
        csv_writer.writerow(out_row)


def main():
    if len(sys.argv) != 4:
        print("{} <url_list> <data_dir> <output_csv_file>".format(sys.argv[0]))
        return

    url_list = sys.argv[1]
    data_dir = sys.argv[2]
    output_csv_file = sys.argv[3]

    out_f = open(output_csv_file, "w", encoding="utf-8")

    csv_writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES, lineterminator="\n")
    csv_writer.writeheader()

    in_f = open(url_list, "r")
    csv_reader = csv.DictReader(in_f)

    for in_row in csv_reader:
        xlsx_url = in_row.get("url")
        xlsx_filepath = in_row.get("filename")
        xlsx_filepath = os.path.join(data_dir, xlsx_filepath)

        print(xlsx_filepath, xlsx_url)

        wrangle_data(xlsx_filepath, xlsx_url, csv_writer)

    in_f.close()
    out_f.close()


if __name__ == "__main__":
    main()
