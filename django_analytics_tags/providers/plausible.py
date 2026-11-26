from django.core.exceptions import ImproperlyConfigured
from django.utils.html import format_html

from . import required_string, script_url

# Fixed upstream bootstrap, not configurable JavaScript. See README for its source.
INITIALIZER = (
    "<script>\n"
    "window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},"
    "plausible.init=plausible.init||function(i){plausible.o=i||{}};\n"
    "plausible.init()\n"
    "</script>"
)


def render(config):
    domain = required_string(config, "DOMAIN_ID")
    if any(char.isspace() for char in domain) or "://" in domain or "/" in domain:
        raise ImproperlyConfigured(
            "ANALYTICS['DOMAIN_ID'] must be a domain, not a URL, for Plausible."
        )
    url = script_url(config)
    mode = config.get("SCRIPT_MODE", "current")
    if mode == "legacy":
        return format_html(
            '<script defer data-domain="{}" src="{}"></script>', domain, url
        )
    if mode != "current":
        raise ImproperlyConfigured(
            "ANALYTICS['SCRIPT_MODE'] must be 'current' or 'legacy'."
        )
    return format_html(
        '<script async src="{}" data-domain="{}"></script>\n'
        + INITIALIZER.replace("{", "{{").replace("}", "}}"),
        url,
        domain,
    )
