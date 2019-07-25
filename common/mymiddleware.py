from django.http import HttpResponseNotFound

class RedirectToNoSlash():
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_request(self, request):
        if '/admin' not in request.path and request.path != '/':
            if request.path[-1] == '/':
                return HttpResponseNotFound(request.path)
