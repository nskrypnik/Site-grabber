# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from scrapy.contrib.pipeline.media import MediaPipeline
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.link import Link
from scrapy.http import Request

class GLink(Link):
    __slots__ = ['url', 'text', 'fragment', 'nofollow', 'raw_url']

    def __init__(self, url, text='', fragment='', nofollow=False, raw_url=''):
        self.url = url
        self.text = text
        self.fragment = fragment
        self.nofollow = nofollow
        self.raw_url = raw_url

class GrabberLinkExtractor(SgmlLinkExtractor):
    '''
        Override SgmlLinkExtractor just to add raw_url
        property to returned links objects
    '''
    def unknown_starttag(self, tag, attrs):
        if tag == 'base':
            self.base_url = dict(attrs).get('href')
        if self.scan_tag(tag):
            for attr, value in attrs:
                if self.scan_attr(attr):
                    url = self.process_value(value)
                    if url is not None:
                        link = GLink(url=url, raw_url=value)
                        self.links.append(link)
                        self.current_link = link


class SaveGrabbedPipeline(object):
    '''
        Save page to Data Base. Should be executed last after all pipelines
    '''
    def process_item(self, item, spider):
        return item

class GrabImagesPipeline(MediaPipeline):

    PAGE_IMAGES = {}
    LOCAL_IMAGES_URI = {}

    def __init__(self, *args, **kw):
        super(GrabImagesPipeline, self).__init__(*args, **kw)
        self.link_extractor = GrabberLinkExtractor(tags=['img', ], attrs=['src', ], deny_extensions=[], canonicalize=False)
    
    def get_media_requests(self, item, info):
        links = self.link_extractor.extract_links(item['response'])
        self.PAGE_IMAGES[item['uri']] = []
        for link in links:
             self.PAGE_IMAGES[item['uri']].append(link.url)
             item['content'] = item['content'].replace(link.raw_url, link.url)
        return [Request(l.url) for l in links]
        
    def media_to_download(self, request, info):
        """Check request before starting download"""
        pass
    
    def media_downloaded(self, response, request, info):
        """Handler for success downloads"""
        return response
        
    def item_completed(self, results, item, info):
        return item
