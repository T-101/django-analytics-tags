"""Configuration validation shared by the two providers."""

from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured


def required_string(config, name):
    value = config.get(name)
    if not isinstance(value, str) or not value.strip():
        raise ImproperlyConfigured(f"ANALYTICS['{name}'] must be a non-empty string.")
    return value


def script_url(config):
    value = required_string(config, "SCRIPT_URL")
    try:
        parsed = urlsplit(value)
        valid = parsed.scheme in {"http", "https"} and parsed.hostname
        parsed.port  # Reject malformed port numbers as well.
    except ValueError:
        valid = False
    if not valid or any(char.isspace() or ord(char) < 32 for char in value):
        raise ImproperlyConfigured(
            "ANALYTICS['SCRIPT_URL'] must be a full HTTP or HTTPS URL."
        )
    return value
