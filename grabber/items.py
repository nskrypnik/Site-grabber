# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class GrabberItem(Item):
    # define the fields for your item here like:
    # name = Field()
    pass
    
class WebPageItem(Item):
    uri = Field()
    content = Field()
    response = Field()
    css = Field() # Shows if the given page is css or not