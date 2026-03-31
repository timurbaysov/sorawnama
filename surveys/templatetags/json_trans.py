import json
import os
from django import template
from django.conf import settings

register = template.Library()

# Загружаем JSON с переводами в память один раз при старте
TRANSLATIONS_FILE = os.path.join(settings.BASE_DIR, 'surveys', 'translations.json')
try:
    with open(TRANSLATIONS_FILE, 'r', encoding='utf-8') as f:
        TRANSLATIONS = json.load(f)
except Exception:
    TRANSLATIONS = {}

@register.simple_tag(takes_context=True)
def t(context, key):
    """
    Тег для перевода по JSON файлу.
    Использование: {% t "Слово на русском" %}
    """
    request = context.get('request')
    lang = (getattr(request, "LANGUAGE_CODE", "uz") or "uz").split("-")[0]
    
    # Ищем перевод
    if key in TRANSLATIONS:
        return TRANSLATIONS[key].get(lang, key)
    
    # Если ключа нет в JSON, возвращаем сам ключ
    return key
