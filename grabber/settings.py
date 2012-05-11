# Scrapy settings for grabber project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#

import os
from ConfigParser import ConfigParser

INI_CONFIG_FILE = os.environ.get('GRABBER_INI_CONFIG_FILE')

if INI_CONFIG_FILE is None:
    INI_CONFIG_FILE = 'development.ini'

parser = ConfigParser(defaults=dict(here=os.getcwd()))
parser.readfp(open(INI_CONFIG_FILE))

WEB_APP_SETTINGS = dict(parser.items('app:main'))

BOT_NAME = 'grabber'
BOT_VERSION = '1.0'

SPIDER_MODULES = ['grabber.spiders']
NEWSPIDER_MODULE = 'grabber.spiders'
USER_AGENT = '%s/%s' % (BOT_NAME, BOT_VERSION)

ITEM_PIPELINES = [
                    #'scrapy.contrib.pipeline.images.ImagesPipeline',
                    'grabber.pipelines.GrabberPipeline',   
                 ]
IMAGES_STORE = os.path.join(os.getcwd(), 'sitegrabber', 'static', 'upload')
