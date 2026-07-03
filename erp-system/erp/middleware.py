from django.shortcuts import redirect

EXEMPT_URLS = {'/', }
EXEMPT_PREFIXES = ('/login/', '/admin/', '/static/', '/media/')


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info
            if path not in EXEMPT_URLS and not any(path.startswith(p) for p in EXEMPT_PREFIXES):
                next_url = request.get_full_path()
                return redirect(f'/login/?next={next_url}')
        return self.get_response(request)
