from .core import OpenstackConnector
from .exception import AtelierException
from .utils import is_valid_uuid, is_valid_ipv4
from netbox.search import LookupTypes

class NovaIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_full_path().startswith('/search/') and 'q' in request.GET:
            request_body = request.GET['q']
            if is_valid_uuid(request_body, 4):
                try:
                    os_connector = OpenstackConnector()
                    id = os_connector.get_baremetal_node_id_from_nova(request_body)
                    if id is not None:
                        new_request_get = request.GET.copy()
                        new_request_get['q'] = id
                        request.GET = new_request_get
                except AtelierException:
                    pass
        
        response = self.get_response(request)
        return response

class NeutronIpMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_full_path().startswith('/search/') and 'q' in request.GET:
            request_body = request.GET['q']
            if is_valid_ipv4(request_body):
                try:
                    os_connector = OpenstackConnector()
                    ids = os_connector.get_baremetal_node_id_from_neutron(request_body)
                    if ids is not []:
                        new_request_get = request.GET.copy()
                        new_request_get['q'] = '|'.join(id for id in ids)
                        new_request_get['lookup'] = LookupTypes.REGEX
                        request.GET = new_request_get
                except AtelierException:
                    pass
        
        response = self.get_response(request)
        return response
