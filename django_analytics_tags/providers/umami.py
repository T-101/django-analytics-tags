from django.utils.html import format_html

from . import required_string, script_url


def render(config):
    domain_id = required_string(config, "DOMAIN_ID")
    url = script_url(config)
    return format_html(
        '<script defer src="{}" data-website-id="{}"></script>', url, domain_id
    )
