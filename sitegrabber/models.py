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

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)    

Base = declarative_base(cls=Base)

class WebPage(Base):
    uri = Column(String(256), nullable=False)
    content = Column(Text) # Site body and content
    website_id = Column(Integer(), ForeignKey('website.id'))
    website = relation('WebSite', backref='pages')
    
class WebSite(Base):
    original_url = Column(String(256), nullable=False)
    local_domain = Column(String(256), nullable=False)
    descr = Column(Text) # Site description
    status = Column(Integer(), default=0) # Status of site indexing
    last_indexed = Column(DateTime())
    created = Column(DateTime(), default=func.now())
