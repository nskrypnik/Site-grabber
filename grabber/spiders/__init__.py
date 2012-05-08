# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import sys

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy import log

from sitegrabber.models import DBSession, Base
from grabber.settings import WEB_APP_SETTINGS
from sqlalchemy import engine_from_config

class GrabberSpider(BaseSpider):
    name = "grabber"
    allowed_domains = ["*"]
    
    # Let's think how to pass here url
    start_urls = [
        'http://www.lierd.com/english/'
    ]
    
    def __init__(self, *args, **kw):
        super(GrabberSpider, self).__init__(*args, **kw)
        log.msg('Init SQL alchemy engine', level=log.DEBUG)
        engine = engine_from_config(WEB_APP_SETTINGS, 'sqlalchemy.')
        DBSession.configure(bind=engine)
        Base.metadata.create_all(engine) # while use creating DB here

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        for url in hxs.select('//a/@href').extract():
            log.msg(url, level=log.DEBUG)
            
        for css in hxs.select('//link/@href').extract():
            log.msg(css, level=log.DEBUG)
            
        for img in hxs.select('//img/@src').extract():
            log.msg(img, level=log.DEBUG)
            
        for js in hxs.select('//script/@src').extract():
            log.msg(js, level=log.DEBUG)
