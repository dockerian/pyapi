
from pyramid.view import view_defaults


@view_defaults(route_name='home')
class HomeViews(object):
    def __init__(self, request):
        self.request = request

    def get(self):
        return {'project': 'localapi'}
