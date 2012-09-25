# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

import os
import hashlib
import re
import cssutils
from cssutils.css import CSSStyleSheet
from scrapy.contrib.pipeline.media import MediaPipeline
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.link import Link
from scrapy.http import Request
from scrapy.selector import HtmlXPathSelector
from grabber.settings import WEB_APP_SETTINGS
from sitegrabber.models import WebPage, StyleSheet
from scrapy import log

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
        if item['css']:
            klass = StyleSheet
        else:
            klass = WebPage
        klass.add(uri=item['uri'], content=item['content'],
            website=spider.website, session=spider.dbsession)
        spider.dbsession.commit()
        return item


class GrabMediaPipeline(MediaPipeline):
    '''
        Abstract pipline class for grabbing all media from page:
        images, javascripts, swf files.
    '''

    link_extractor = None

    def __init__(self, *args, **kw):
        super(GrabMediaPipeline, self).__init__(*args, **kw)
        self.media_store_path = WEB_APP_SETTINGS.get('downloaded.path')
        self.media_local_url = WEB_APP_SETTINGS.get('downloaded.url')
        self.PAGE_MEDIA = {}
        self.LOCAL_MEDIA_URI = {}

    def get_media_checksum(self, media_data):
        '''
            Get checksum for downloaded media
        '''
        checksum = hashlib.sha1()
        pos = 0
        chunk_size = 1024
        while pos < len(media_data):
            checksum.update(media_data[pos: pos + chunk_size])
            pos += chunk_size
        return checksum.hexdigest()

    def get_media_name(self, media_url):
        return media_url.split('/')[-1]

    def save_media_to_file(self, media_name, checksum, media_data):
        media_dir_path = os.path.join(self.media_store_path, checksum)
        if not os.path.exists(media_dir_path):
            os.mkdir(media_dir_path)
        else:
            '''
                Such image is already exists
            '''
        media_path = os.path.join(self.media_store_path, checksum, media_name)
        media_file = open(media_path, 'wb')
        media_file.write(media_data)

    def get_media_requests(self, item, info):
        links = self.link_extractor.extract_links(item['response'])
        self.PAGE_MEDIA[item['uri']] = []
        for link in links:
            self.PAGE_MEDIA[item['uri']].append(link.url)
            item['content'] = item['content'].replace(link.raw_url, link.url)
        return [Request(l.url) for l in links]

    def media_to_download(self, request, info):
        """Check request before starting download"""
        pass

    def media_downloaded(self, response, request, info):
        """
            Handler for success downloads. Here it would be good to
            make some hash from downloaded image and save to specific
            path downloaded image
        """
        referer = request.headers.get('Referer')

        if response.status != 200:
            err_msg = 'Media (code: %s): Error downloading media from %s referred in <%s>' % (response.status, request, referer)
            log.msg(err_msg, level=log.WARNING, spider=info.spider)
            raise Exception(err_msg)

        if not response.body:
            err_msg = 'Media (empty-content): Empty Media from %s referred in <%s>: no-content' % (request, referer)
            log.msg(err_msg, level=log.WARNING, spider=info.spider)
            raise Exception(err_msg)

        status = 'cached' if 'cached' in response.flags else 'downloaded'

        media_name = self.get_media_name(response.url)
        checksum = self.get_media_checksum(response.body)
        local_url = "%s%s/%s" % (self.media_local_url, checksum, media_name)

        self.save_media_to_file(media_name, checksum, response.body)

        self.process_media(response)

        return dict(url=response.url, checksum=checksum,
                    media_name=media_name, local_url=local_url)

    def item_completed(self, results, item, info):
        item_content = item['content']
        for success, result in results:
            if not success:
                raise result
            else:
                item_content = item_content.replace(result['url'],
                    result['local_url'])
        item['content'] = item_content
        return item

    def process_media(self, response):
        pass


class GrabberImagesPipeline(GrabMediaPipeline):
    '''
        Grab all images both from css and html pages
    '''

    link_extractor = GrabberLinkExtractor(tags=['img', 'input'],
        attrs=['src', ], deny_extensions=[], canonicalize=False)

    def get_links_from_css(self, style_text, item):
        '''
            This function extracts urls from css style text
            and returns requests for download thees images.
            Also in this function we are replacing urls to
            absolute uri to replace it by local url
        '''
        response = item['response']
        sheet = CSSStyleSheet()
        sheet.cssText = style_text
        urls = cssutils.getUrls(sheet)
        requests = []
        item_content = item['content']
        for url in urls:
            request_url = response.url.replace('http://', '')
            if url[0] == '/':
                request_url = request_url.split('/')[0] + url
            else:
                request_url = request_url.split('/')
                request_url[-1] = url
                request_url = '/'.join(request_url)
            request_url = 'http://%s' % request_url
            item_content = item_content.replace(url, request_url)
            requests.append(Request(request_url))
        item['content'] = item_content
        return requests

    def get_media_requests(self, item, info):
        requests = \
            super(GrabberImagesPipeline, self).get_media_requests(item, info)
        if item['css']:
            requests.extend(self.get_links_from_css(item['content'], item))
        else:
            #try to find in html style tags and parse it's content
            hxcs = HtmlXPathSelector(item['response'])
            for style_text in hxcs.select('//style/text()').extract():
                requests.extend(self.get_links_from_css(style_text, item))

        return requests


class GrabberJSPipeline(GrabMediaPipeline):
    link_extractor = GrabberLinkExtractor(tags=['script', ],
        attrs=['src', ], deny_extensions=[], canonicalize=False)


class GrabberSWFPipeline(GrabMediaPipeline):
    '''
        Grab embedded objects(swf) from page
    '''
    link_extractor = GrabberLinkExtractor(tags=['embed', ], attrs=['src', ],
        deny_extensions=[], canonicalize=False)


class GarbberCSSImagePipeline(GrabMediaPipeline):
    '''
        Grab images from css files
    '''

    def process_item(self, item, spider):
        ' work just with css pages '
        if item['css']:
            return super(GarbberCSSImagePipeline, self)\
                .process_item(item, spider)
        return item

    def get_media_requests(self, item, info):
        sheet = CSSStyleSheet()
        sheet.cssText = item['content']
        urls = cssutils.getUrls(sheet)
        return [Request(u) for u in urls]
