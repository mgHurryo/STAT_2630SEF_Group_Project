# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class RatingItem(scrapy.Item):
    # define the fields for your item here like:
    season=scrapy.Field()
    rating=scrapy.Field()
    total_people=scrapy.Field()
    # name = scrapy.Field()
    pass
