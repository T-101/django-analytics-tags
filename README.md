# django-analytics-tags

Add Plausible or Umami Analytics to Django with one template tag, using either
hosted or self-hosted scripts. Django is the only runtime dependency: no database,
middleware, context processors, or static files. The package makes no HTTP
requests and collects no telemetry; tracking runs in the visitor's browser.

Requires Python 3.11+ and Django 4.2–6.1. Django 4.2 supports Python 3.11/3.12
(3.12 requires 4.2.8+); Django 6.x requires Python 3.12+.
[Upstream security support](https://www.djangoproject.com/download/#supported-versions)
still follows Django's release lifecycle.

## Installation

```sh
python -m pip install django-analytics-tags
```

Add the app to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    "django_analytics_tags",
]
```

Place the tag once inside your base template's `<head>`:

```django
{% load django_analytics_tags %}
{% django_analytics_tags %}
```

## Configuration

Set `ANALYTICS` in Django settings. All three values are required when enabled:

| Setting | Meaning |
| --- | --- |
| `PROVIDER` | `"plausible"` or `"umami"` |
| `DOMAIN_ID` | Plausible: the tracked domain. Umami: the website ID from its tracking code. |
| `SCRIPT_URL` | Full HTTP or HTTPS script URL, including its path. No built-in URLs or defaults. |

### Umami

```python
ANALYTICS = {
    "PROVIDER": "umami",
    "DOMAIN_ID": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "SCRIPT_URL": "https://analytics.example.com/script.js",
}
```

Use your hosted or self-hosted script URL from
[Umami's tracking code](https://docs.umami.is/docs/collect-data).
The tag renders a `defer` script with `DOMAIN_ID` as `data-website-id`.

### Plausible

```python
ANALYTICS = {
    "PROVIDER": "plausible",
    "DOMAIN_ID": "example.com",
    "SCRIPT_URL": "https://plausible.io/js/pa-YOUR-SITE-ID.js",
}
```

Copy your personalized URL from **Site settings → General → Site installation**.
The tag renders an asynchronous script and Plausible's
[official inline initializer](https://plausible.io/docs/proxy/guides/nginx).
`DOMAIN_ID` is rendered as `data-domain`; current hosted scripts identify the
site through their personalized URL.

For a self-hosted instance using the older `defer` / `data-domain` snippet:

```python
ANALYTICS = {
    "PROVIDER": "plausible",
    "DOMAIN_ID": "example.com",
    "SCRIPT_URL": "https://plausible.example.com/js/script.js",
    "SCRIPT_MODE": "legacy",
}
```

Plausible's `SCRIPT_MODE` accepts `"current"` (default, with initializer) or
`"legacy"` (external script only). Match your instance's installation snippet;
the package does not infer the mode from the URL.

### Disabling tracking and environment variables

Missing `ANALYTICS`, `None`, `{}`, or an omitted or empty `PROVIDER` renders
nothing, without warnings. A selected provider with missing or invalid settings
raises `django.core.exceptions.ImproperlyConfigured` when rendered.

Read environment variables in your project's settings, for example:

```python
import os

ANALYTICS = None
if os.environ.get("ANALYTICS_ENABLED", "").lower() == "true":
    ANALYTICS = {
        "PROVIDER": os.environ.get("ANALYTICS_PROVIDER", ""),
        "DOMAIN_ID": os.environ.get("ANALYTICS_DOMAIN_ID", ""),
        "SCRIPT_URL": os.environ.get("ANALYTICS_SCRIPT_URL", ""),
    }
```

Set the flag to `true` and provide the three values to enable tracking. Leave it
unset or set it to `false` to disable tracking. The package never reads the environment.

## Security

Dynamic attributes are escaped with Django's `format_html()`; normal template
autoescaping is preserved. Script URLs are trusted deployment configuration:
browsers execute JavaScript from the configured source, so use sources you trust
and prefer HTTPS. There is no setting for raw HTML or JavaScript.

If using Content Security Policy, allow the script source and, for current
Plausible scripts, the fixed inline initializer (for example, through a hash of
its exact rendered contents).

## Development

From a checkout, in a virtual environment:

```sh
python -m pip install -e .
python -m django test tests --settings=tests.settings
./build.sh
```

Tests use Django and standard `unittest`, with no test database required.

## License

Copyright (c) 2026 [T-101](https://github.com/T-101/).
Licensed under the [MIT License](LICENSE).
