from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNotFound, HTTPFound
from .models import WebSite, WebResource

from sqlalchemy.exc import DBAPIError


@view_config(context='pyramid.httpexceptions.HTTPNotFound')
def not_found_handler(request):
    '''
        Usually in our application we use this view.
    '''
    host = request.host.split(':')[0] # get url of instance
    site = WebSite.get(host)

    if site:
        uri = request.path_qs
        resource = WebResource.get(uri, site.id)
        if resource is None and uri[-1] != '/':
            uri += '/'
            return HTTPFound(uri)
        if resource:
            return Response(resource.content)
        else:
            #TODO: try here to proxy request for original site
            return HTTPNotFound('Not found in cache')
    else: return HTTPNotFound('No such site in database')



