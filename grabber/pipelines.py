# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/topics/item-pipeline.html

from scrapy.contrib.pipeline.media import MediaPipeline
from scrapy.contrib.pipeline.images import ImagesPipeline
scrapy.contrib.linkextractors.sgml.SgmlLinkExtractor

class GrabberPipeline(object):
    def process_item(self, item, spider):
        return item

class GrabImagesPipeline(MediaPipeline):

    def __init__(self, *args, **kw):
        super(GrabImagesPipeline, self).__init__(*args, **kw)
        self.link_extractor = SgmlLinkExtractor(tags=('img', ), attrs=('src', ))
    
    def get_media_requests(self, item, info):
        pass
    
