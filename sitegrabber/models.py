from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    Unicode,
    DateTime,
    ForeignKey,
    )
    
from sqlalchemy.orm import relation
from sqlalchemy.sql.expression import *

from sqlalchemy.ext.declarative import declarative_base, declared_attr

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

class Base(object):

    session = DBSession # static propery may be overrided for some purposes

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)    

Base = declarative_base(cls=Base)

class WebResource(Base):

    HTML_TYPE = 1
    CSS_TYPE  = 2

    uri = Column(String(256), nullable=False, unique=True)
    content = Column(Text) # Site body and content
    website_id = Column(Integer(), ForeignKey('website.id'))
    res_type = Column(Integer())
    website = relation('WebSite', backref='pages')

    __mapper_args__ = {'polymorphic_on': res_type}

    @classmethod
    def get(cls, path, site_id, session=DBSession):
        resource = session.query(WebResource).filter(WebResource.uri == path, WebResource.website_id == site_id).first()
        return resource

    @classmethod
    def add(cls, **kw):
        uri = kw.pop('uri', None)
        session = kw.pop('session', None)
        if session is None: session = DBSession()
        if uri is None:
            raise Exception('uri parameter is required for this function')
            # try to find page with this uri first
        page = session.query(cls).filter(cls.uri == uri).first()
        if page:
            page.__dict__.update(kw)
        else:
            page = cls(uri=uri, **kw)
        session.add(page)
        session.flush()

    @classmethod
    def exists(cls, url):
        page = cls.session.query(cls).filter(cls.uri == url).first()
        return page

class WebPage(WebResource):
    '''
        Web page
    '''
    __tablename__ = None
    __mapper_args__ = {'polymorphic_identity': WebResource.HTML_TYPE}

class StyleSheet(WebResource):
    __tablename__ = None
    __mapper_args__ = {'polymorphic_identity': WebResource.CSS_TYPE}


class MediaResource():
    '''
        Represents media resources like javascript, images, embedded flash
        objects(instead of css, that we assume is web resource like page)
    '''
    #TODO: while it's unused. But it will be

class WebSite(Base):
    original_url = Column(String(256), nullable=False, unique=True)
    local_domain = Column(String(256), nullable=False)
    descr = Column(Text) # Site description
    status = Column(Integer(), default=0) # Status of site indexing
    last_indexed = Column(DateTime())
    created = Column(DateTime(), default=func.now())

    @classmethod
    def get(cls, local_doamin, session=None):
        if session is None:
            session = DBSession()
        site = session.query(WebSite).filter(WebSite.local_domain == local_doamin).first()
        return site


