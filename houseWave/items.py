# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HousewaveItem(scrapy.Item):
    # define the fields for your item here like:
    city = scrapy.Field()
    index = scrapy.Field()
    types = scrapy.Field()
    year = scrapy.Field()
    month = scrapy.Field()
    pass
