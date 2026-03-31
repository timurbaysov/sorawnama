from django.conf import settings
from django.utils import translation


class SessionLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.valid_codes = {item[0] for item in settings.LANGUAGES}

    def __call__(self, request):
        lang = request.session.get("site_language", "uz")
        if lang not in self.valid_codes:
            lang = "uz"
        translation.activate(lang)
        request.LANGUAGE_CODE = lang
        response = self.get_response(request)
        translation.deactivate()
        return response
