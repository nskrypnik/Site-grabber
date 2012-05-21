# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

import os
import hashlib
from scrapy.contrib.pipeline.media import MediaPipeline
from scrapy.contrib.pipeline.images import ImagesPipeline
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.link import Link
from scrapy.http import Request
from grabber.settings import WEB_APP_SETTINGS

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
        self.img_store_path = WEB_APP_SETTINGS.get('downloaded.path')
        self.img_local_url = WEB_APP_SETTINGS.get('downloaded.url')


    def get_image_checksum(self, image_data):
        '''
            Get checksum for downloaded media
        '''
        checksum = hashlib.sha1()
        pos = 0
        chunk_size = 1024
        while pos < len(image_data):
            checksum.update(image_data[pos: pos+chunk_size])
            pos += chunk_size
        return checksum.hexdigest()

    def get_image_name(self, img_url):
        return img_url.split('/')[-1]

    def save_img_to_file(self, img_name, checksum, img_data):
        img_dir_path = os.path.join(self.img_store_path, checksum)
        if not os.path.exists(img_dir_path):
            os.mkdir(img_dir_path)
        else:
            '''
                Such image is already exists
            '''
        img_path = os.path.join(self.img_store_path, checksum, img_name)
        img_file = open(img_path, 'wb')
        img_file.write(img_data)

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
        """
            Handler for success downloads. Here it would be good to
            make some hash from downloaded image and save to specific
            path downloaded image
        """
        referer = request.headers.get('Referer')

        if response.status != 200:
            log.msg('Image (code: %s): Error downloading image from %s referred in <%s>'\
            % (response.status, request, referer), level=log.WARNING, spider=info.spider)
            raise ImageException

        if not response.body:
            log.msg('Image (empty-content): Empty image from %s referred in <%s>: no-content'\
            % (request, referer), level=log.WARNING, spider=info.spider)
            raise ImageException

        status = 'cached' if 'cached' in response.flags else 'downloaded'

        img_name = self.get_image_name(response.url)
        checksum = self.get_image_checksum(response.body)
        local_url = "%s%s/%s" % (self.img_local_url, checksum, img_name)

        self.save_img_to_file(img_name, checksum, response.body)

        return dict(url=response.url, checksum=checksum, img_name=img_name, local_url=local_url)


    def item_completed(self, results, item, info):
        import pdb; pdb.set_trace()
        return item
