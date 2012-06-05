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
        path = request.path
        uri = path
        # Construct right url here. For that use GET dictionary with sorted parameters to
        # get well formed url for seeking in database
        if request.path_qs.find('?') != -1:
            query_string = request.path_qs.split('?')[1]
            value_pairs = query_string.split('&')
            value_pairs.sort()
            uri = "%s?%s" % (uri, '&'.join(value_pairs))
        resource = WebResource.get(uri, site.id)
        if resource is None and uri[-1] != '/' and uri.find('?') == -1:
            uri += '/'
            return HTTPFound(uri)
        if resource:
            return Response(resource.content)
        else:
            #TODO: try here to proxy request for original site
            return HTTPNotFound('Not found in cache')
    else: return HTTPNotFound('No such site in database')



