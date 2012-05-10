# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.

import sys
import time

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy import log
from scrapy.http import Request

from sitegrabber.models import DBSession, Base, WebPage, WebSite
from grabber.settings import WEB_APP_SETTINGS
from sqlalchemy import engine_from_config
from sqlalchemy.orm import Session

class GrabberSpider(CrawlSpider):
    name = "grabber"
    allowed_domains = ["www.lierd.com"]
    
    SCRAPED_URLS = []
    
    # Let's think how to pass here url
    start_urls = [
        'http://www.lierd.com/english/'
    ]
    
    rules = [
        Rule(SgmlLinkExtractor(), callback='parse_item'),
    ]
    
    def __init__(self, *args, **kw):
        SCRAPED_DOMAIN = "www.lierd.com"
        super(GrabberSpider, self).__init__(*args, **kw)
        log.msg('Init SQL alchemy engine', level=log.DEBUG)
        engine = engine_from_config(WEB_APP_SETTINGS, 'sqlalchemy.')
        conn = engine.connect()
        self.dbsession = Session(bind=conn)
        
        # patch orm objects to use this local session object
        WebPage.session = self.dbsession
        
        Base.metadata.create_all(engine) # while use creating DB here
        
        q = self.dbsession.query(WebSite).filter(WebSite.original_url == SCRAPED_DOMAIN)
        website = q.first()
        if website is None:
            website = WebSite(original_url=SCRAPED_DOMAIN, local_domain='test.localhost')
            self.dbsession.add(website)
            self.dbsession.commit()
        self.website = website
        
    
    def prepare_link(self, url, current_url):
        '''
            Make proper uri from given url
        '''
        if not current_url.endswith('/'): current_url += '/'
        
        # ignore javascript links
        for s in ['javascript:', 'mailto:', '#']:
            if url.startswith(s): return None
        
        if url.find('http://') != -1 or url.find('https://') != -1:
            # in case we have complete http or https protocol uri
            url = url.replace('http://', '').replace('https://', '')
            url_domain = url.split('/')[0]
            if url_domain == self.website.original_url: return url # Scrape just this site urls
            else: return None # don't scrape external links
        
        if url.startswith('/'):
            # we get absolute url
            return "http://%s%s" % (self.website.original_url, url)
        else:
            return "%s%s" % (current_url, url)
            
        
    def parse_item(self, response):
        
        log.msg('I\'m here: %s' % response.url, level=log.DEBUG)
        if 'text/html' in response.headers['Content-Type']:
            self.handle_page(response)
        hxs = HtmlXPathSelector(response)
        '''
        for css in hxs.select('//link/@href').extract():
            log.msg(css, level=log.DEBUG)
            
        for img in hxs.select('//img/@src').extract():
            log.msg(img, level=log.DEBUG)
            
        for js in hxs.select('//script/@src').extract():
            log.msg(js, level=log.DEBUG)
        
        for url in hxs.select('//a/@href').extract():
            log.msg('Going by link %s' % url, level=log.DEBUG)
            if WebPage.exists(self._get_path(url)):
                continue
            url = self.prepare_link(url, response.url)
            if not url:
                continue
            if url in self.__class__.SCRAPED_URLS: continue
            self.__class__.SCRAPED_URLS.append(url)
            time.sleep(0.1)
            yield Request(url, callback=self.parse)
        '''

    
    def _get_path(self, url):
        path = url.replace('http://', '')
        path = path.split('/')
        path[0] = ''
        return '/'.join(path)
    
    def handle_page(self, response):
        path = self._get_path(response.url)
        log.msg('Scraping page %s' % path, level=log.DEBUG)
        content = response.body.decode(response.encoding)
        WebPage.add(uri=path, content=content, website=self.website)
        self.dbsession.commit()
