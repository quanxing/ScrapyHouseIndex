# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re

class HousewavePipeline(object):
    """
    #拿到url然后再处理
    """
    def process_item(self, item, spider):
        return item
