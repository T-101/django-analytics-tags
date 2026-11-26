from django import template
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_analytics_tags.providers import plausible, umami

register = template.Library()


@register.simple_tag
def django_analytics_tags():
    config = getattr(settings, "ANALYTICS", None)
    if config is None:
        return ""
    if not isinstance(config, dict):
        raise ImproperlyConfigured("ANALYTICS must be a dictionary or None.")
    provider = config.get("PROVIDER", "")
    if provider == "":
        return ""
    if not isinstance(provider, str):
        raise ImproperlyConfigured("ANALYTICS['PROVIDER'] must be a lowercase string.")
    if provider == "plausible":
        return plausible.render(config)
    if provider == "umami":
        return umami.render(config)
    raise ImproperlyConfigured(f"Unknown ANALYTICS provider: {provider!r}.")
