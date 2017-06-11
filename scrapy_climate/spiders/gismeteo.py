# -*- coding: utf-8 -*-

import scrapy

from ..items import EventItem, ScrapedUrlsItem
from ..tools import convert_list_to_string


class GismeteoSpider(scrapy.Spider):
    name = 'gismeteo'
    allowed_domains = ['www.gismeteo.ua']
    start_urls = ['https://www.gismeteo.ua/news/']

    def parse(self, response: scrapy.http.Response):
        # locate `div`s with news
        news = response.css('.item')
        indexes = []
        for selector in news:
            path = selector.xpath('div[@class="item__title"]/a/@href').extract_first()
            url = 'https://{host}{path}'.format(host=self.allowed_domains[0], path=path)
            index = self._extract_index_from_path(path)
            indexes.append(index)
            yield scrapy.http.Request(url=url,
                                      callback=self.parse_article,
                                      meta={'index': index})
        # create item, which be used to store new indexes (see Pipeline)
        yield ScrapedUrlsItem(tmp_list=indexes)

    def parse_article(self, response: scrapy.http.Response):
        # locate article
        article = response.css('.article')
        # generate `tags` string
        tags_list = article.xpath('div[@class="article__tags links-grey"]/a/text()').extract()
        tags = convert_list_to_string(tags_list, ',')
        # generate `text` string
        text_blocks = article.xpath('div[@class="article__i ugc"]/div/text()').extract()
        text = convert_list_to_string(text_blocks, '', handler=self._clear_text_field)
        # produce item
        yield EventItem(
            url=response.url,
            header=article.xpath('div[@class="article__h"]/h1/text()').extract_first(),
            tags=tags,
            text=text,
            index=response.meta['index']
        )

    def _clear_text_field(self, text: str) -> str:
        string = str(text).replace('\xa0', ' ')
        return string.replace('\n', '')

    def _extract_index_from_path(self, path: str) -> str:
        """ function that extracts unique part from given url."""
        # left only event index
        return path.split('/')[-2].split('-')[0]
