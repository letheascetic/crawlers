# coding: utf-8

from homelink.spiders.sx import SxSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


if __name__ == '__main__':
    process = CrawlerProcess(get_project_settings())
    process.crawl(SxSpider)
    process.start()
    pass


