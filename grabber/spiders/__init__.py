# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import sys
import transaction

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy import log
from scrapy.http import Request

from sitegrabber.models import DBSession, Base, WebPage, WebSite
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
        
        q = DBSession.query(WebSite).filter(WebSite.original_url == "www.lierd.com")
        website = q.first()
        if website is None:
            website = WebSite(original_url="www.lierd.com", local_domain='test.localhost')
            DBSession.add(website)
            DBSession.flush()
            transaction.commit()
        self.website = website
        
    def parse(self, response):
        
        self.handle_page(response)
    
        hxs = HtmlXPathSelector(response)
            
        for css in hxs.select('//link/@href').extract():
            log.msg(css, level=log.DEBUG)
            
        for img in hxs.select('//img/@src').extract():
            log.msg(img, level=log.DEBUG)
            
        for js in hxs.select('//script/@src').extract():
            log.msg(js, level=log.DEBUG)

        for url in hxs.select('//a/@href').extract():
            yield Request(url, callback=self.parse)

    
    def _get_path(self, url):
        path = url.replace('http://', '')
        path = path.split('/')
        path[0] = ''
        return '/'.join(path)
    
    def handle_page(self, response):
        path = self._get_path(response.url)
        log.msg('Scraping page %s' % path, level=log.DEBUG)
        page = WebPage(uri=path, content=response.body, website=self.website)
        DBSession.add(page)
        DBSession.flush()
        transaction.commit()
