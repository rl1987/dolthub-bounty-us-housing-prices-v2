# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

# https://www.dolthub.com/repositories/dolthub/us-housing-prices-v2/query/main?q=SHOW+CREATE+TABLE+%60sales%60&active=Schemas
# https://www.dolthub.com/repositories/dolthub/us-housing-prices-v2/doc/main
class SalesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    state = scrapy.Field()
    property_zip5 = scrapy.Field()
    property_street_address = scrapy.Field()
    property_city = scrapy.Field()
    property_county = scrapy.Field()
    property_id = scrapy.Field()
    sale_datetime = scrapy.Field()
    property_type = scrapy.Field()
    sale_price = scrapy.Field()
    seller_1_name = scrapy.Field()
    buyer_1_name = scrapy.Field()
    building_num_units = scrapy.Field()
    building_year_built = scrapy.Field()
    source_url = scrapy.Field()
    book = scrapy.Field()
    page = scrapy.Field()
    transfer_deed_type = scrapy.Field()
    property_township = scrapy.Field()
    property_lat = scrapy.Field()
    property_lon = scrapy.Field()
    sale_id = scrapy.Field()
    deed_date = scrapy.Field()
    building_num_stories = scrapy.Field()
    building_num_beds = scrapy.Field()
    building_num_baths = scrapy.Field()
    building_area_sqft = scrapy.Field()
    building_assessed_value = scrapy.Field()
    building_assessed_date = scrapy.Field()
    land_area_acres = scrapy.Field()
    land_area_sqft = scrapy.Field()
    land_assessed_value = scrapy.Field()
    seller_2_name = scrapy.Field()
    buyer_2_name = scrapy.Field()
    land_assessed_date = scrapy.Field()
    seller_1_state = scrapy.Field()
    seller_2_state = scrapy.Field()
    buyer_1_state = scrapy.Field()
    buyer_2_state = scrapy.Field()
    total_assessed_value = scrapy.Field()
    total_appraised_value = scrapy.Field()
    land_appraised_value = scrapy.Field()
    building_appraised_value = scrapy.Field()
    land_type = scrapy.Field()
