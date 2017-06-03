# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsListItem(scrapy.Item):
    url = scrapy.Field()
    header = scrapy.Field()
    description = scrapy.Field()
    tag = scrapy.Field()


class LatestNewsIdItem(scrapy.Item):
    index = scrapy.Field()
