from html.parser import HTMLParser

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.template import Context, Template
from django.test import SimpleTestCase, override_settings


class Scripts(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class AnalyticsTests(SimpleTestCase):
    def render(self, config):
        with override_settings(ANALYTICS=config):
            return Template("{% load django_analytics_tags %}{% django_analytics_tags %}").render(Context())

    def test_app_installed_without_configuration(self):
        self.assertTrue(apps.is_installed("django_analytics_tags"))
        self.assertEqual(
            Template("{% load django_analytics_tags %}{% django_analytics_tags %}").render(Context()), ""
        )

    def test_disabled(self):
        for config in (None, {}, {"PROVIDER": ""}, {"DOMAIN_ID": "example.com"}):
            with self.subTest(config=config):
                self.assertEqual(self.render(config), "")

    def test_umami_hosted_explicit_url(self):
        self.assertEqual(
            self.render({"PROVIDER": "umami", "DOMAIN_ID": "test-website",
                         "SCRIPT_URL": "https://cloud.umami.is/script.js"}),
            '<script defer src="https://cloud.umami.is/script.js" '
            'data-website-id="test-website"></script>',
        )

    def test_umami_self_hosted(self):
        self.assertEqual(
            self.render({"PROVIDER": "umami", "DOMAIN_ID": "site", "SCRIPT_URL":
                         "http://localhost:3000/custom.js"}),
            '<script defer src="http://localhost:3000/custom.js" '
            'data-website-id="site"></script>',
        )

    def test_plausible_current_hosted(self):
        html = self.render({"PROVIDER": "plausible", "DOMAIN_ID": "example.com",
                            "SCRIPT_URL": "https://plausible.io/js/pa-site.js"})
        self.assertEqual(Scripts(html).tags, [
            ("script", {"async": None, "src": "https://plausible.io/js/pa-site.js",
                        "data-domain": "example.com"}), ("script", {})])
        self.assertIn("plausible.init()", html)
        self.assertIn("function(){(plausible.q=plausible.q||[]).push(arguments)}", html)

    def test_plausible_current_custom_url(self):
        html = self.render({"PROVIDER": "plausible", "DOMAIN_ID": "example.com",
                            "SCRIPT_URL": "https://stats.internal/pa-site.js"})
        self.assertIn('src="https://stats.internal/pa-site.js"', html)
        self.assertIn("plausible.init()", html)

    def test_plausible_legacy_self_hosted(self):
        self.assertEqual(self.render({"PROVIDER": "plausible", "DOMAIN_ID": "example.com",
                                     "SCRIPT_URL": "https://stats.internal/js/script.js",
                                     "SCRIPT_MODE": "legacy"}),
                         '<script defer data-domain="example.com" '
                         'src="https://stats.internal/js/script.js"></script>')

    def test_missing_required_values(self):
        for config, key in [
            ({"PROVIDER": "umami"}, "DOMAIN_ID"),
            ({"PROVIDER": "plausible"}, "DOMAIN_ID"),
            ({"PROVIDER": "plausible", "DOMAIN_ID": "example.com"}, "SCRIPT_URL"),
            ({"PROVIDER": "umami", "DOMAIN_ID": "site"}, "SCRIPT_URL"),
            ({"PROVIDER": "plausible", "DOMAIN": "example.com",
              "SCRIPT_URL": "https://stats/script.js"}, "DOMAIN_ID"),
            ({"PROVIDER": "umami", "WEBSITE_ID": "site",
              "SCRIPT_URL": "https://stats/script.js"}, "DOMAIN_ID"),
        ]:
            with self.subTest(config=config), self.assertRaisesMessage(ImproperlyConfigured, key):
                self.render(config)

    def test_invalid_configuration_types(self):
        for value in (False, 0, "", "umami", [], ["umami"]):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                self.render(value)

    def test_invalid_providers(self):
        for value in (None, False, 0, [], {}, "UMAMI", "unknown", " "):
            with self.subTest(value=value), self.assertRaises(ImproperlyConfigured):
                self.render({"PROVIDER": value})

    def test_invalid_required_strings(self):
        for provider in ("umami", "plausible"):
            for value in (None, False, 123, [], {}, "", " "):
                with self.subTest(provider=provider, value=value):
                    with self.assertRaisesMessage(ImproperlyConfigured, "DOMAIN_ID"):
                        self.render({"PROVIDER": provider, "DOMAIN_ID": value})

    def test_invalid_script_urls(self):
        for provider in ("umami", "plausible"):
            for url in (None, False, 12, [], "", "script.js", "//stats/script.js",
                        "javascript:alert(1)", "data:text/javascript,alert(1)",
                        "https://", "https://[broken", "https://stats:bad/a.js",
                        "https://stats/a.js\n", "https://stats/a b.js"):
                with self.subTest(provider=provider, url=url):
                    with self.assertRaisesMessage(ImproperlyConfigured, "SCRIPT_URL"):
                        self.render({"PROVIDER": provider, "DOMAIN_ID": "example.com", "SCRIPT_URL": url})

    def test_invalid_domain(self):
        for domain in ("https://example.com", "example.com/path", "example com"):
            with self.subTest(domain=domain), self.assertRaisesMessage(ImproperlyConfigured, "DOMAIN_ID"):
                self.render({"PROVIDER": "plausible", "DOMAIN_ID": domain})

    def test_invalid_plausible_mode(self):
        for mode in (None, False, [], "unknown"):
            with self.subTest(mode=mode), self.assertRaisesMessage(ImproperlyConfigured, "SCRIPT_MODE"):
                self.render({"PROVIDER": "plausible", "DOMAIN_ID": "example.com",
                             "SCRIPT_URL": "https://stats/script.js", "SCRIPT_MODE": mode})

    def test_dynamic_attributes_are_escaped(self):
        payload = '\"><img/src=x/onerror=alert(1)>'
        url = 'https://stats/script.js?x="&y=\'<bad>'
        for provider in ("umami", "plausible"):
            # Plausible DOMAIN_ID disallows slashes; quotes and angle brackets still must be escaped.
            value = payload if provider == "umami" else 'example.com"><img>'
            for mode in ("current", "legacy"):
                with self.subTest(provider=provider, mode=mode):
                    html = self.render({"PROVIDER": provider, "DOMAIN_ID": value,
                                        "SCRIPT_URL": url, "SCRIPT_MODE": mode})
                    tags = Scripts(html).tags
                    self.assertTrue(all(tag == "script" for tag, attrs in tags))
                    self.assertEqual(tags[0][1]["src"], url)
                    attr = "data-website-id" if provider == "umami" else "data-domain"
                    self.assertEqual(tags[0][1][attr], value)
                    self.assertIn("&quot;", html)
                    self.assertIn("&amp;", html)
                    self.assertIn("&lt;", html)

    @override_settings(ANALYTICS={
        "PROVIDER": "umami", "DOMAIN_ID": "site", "SCRIPT_URL": "https://stats/script.js"
    })
    def test_template_autoescaping_is_preserved(self):
        html = Template("{% load django_analytics_tags %}{% django_analytics_tags %}{{ value }}").render(
            Context({"value": "<b>unsafe</b>"})
        )
        self.assertTrue(html.startswith("<script defer"))
        self.assertTrue(html.endswith("&lt;b&gt;unsafe&lt;/b&gt;"))

    def test_settings_changes_are_not_cached(self):
        self.assertIn("<script", self.render({"PROVIDER": "umami", "DOMAIN_ID": "site",
                                              "SCRIPT_URL": "https://stats/script.js"}))
        self.assertEqual(self.render(None), "")
