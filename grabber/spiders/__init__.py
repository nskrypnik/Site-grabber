# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

from scrapy import log

class GrabberSpider(BaseSpider):
    name = "grabber"
    allowed_domains = ["*"]
    
    # Let's think how to pass here url
    start_urls = [
        'http://www.lierd.com/english/'
    ]

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        for url in hxs.select('//a/@href').extract():
            log.msg(url, level=log.DEBUG)
            
        for css in hxs.select('//link/@href').extract():
            log.msg(css, level=log.DEBUG)
            
        for img in hxs.select('//img/@src').extract():
            log.msg(img, level=log.DEBUG)
