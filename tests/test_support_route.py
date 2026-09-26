import os
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from flask import Flask

from routes.seo import CANONICAL_URLS, PUBLIC_ORIGIN, seo
from routes.support import support


class SupportRouteTestCase(unittest.TestCase):
    def setUp(self):
        root = os.path.dirname(os.path.dirname(__file__))
        self.app = Flask(__name__, template_folder=os.path.join(root, "templates"))
        self.app.config.update(TESTING=True, SECRET_KEY="test-secret")
        self.app.jinja_env.globals["csrf_token"] = lambda: "test-csrf-token"

        def placeholder():
            return "placeholder"

        for rule, endpoint in (
            ("/", "main.accueil"),
            ("/privacy", "legal.privacy"),
            ("/cgu", "legal.cgu"),
            ("/mentions-legales", "legal.mentions"),
            ("/connexion", "auth.connexion"),
            ("/inscription", "auth.inscription"),
            ("/convertir", "convert.convertir"),
        ):
            self.app.add_url_rule(rule, endpoint=endpoint, view_func=placeholder)

        self.app.register_blueprint(support)
        self.app.register_blueprint(seo)
        self.client = self.app.test_client()

    def test_get_support_renders_the_public_form(self):
        response = self.client.get("/support")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Support & Assistance', response.data)
        self.assertIn(b'<form method="POST"', response.data)

    def test_support_has_one_self_referencing_canonical(self):
        response = self.client.get("/support", headers={"Host": "old.example"})
        canonical = b'<link rel="canonical" href="https://www.africachangex.com/support">'
        self.assertEqual(response.data.count(canonical), 1)

    def test_incomplete_post_redirects_to_support_without_a_server_error(self):
        response = self.client.post("/support", data={"nom": "Test"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/support")

    def test_valid_post_redirects_to_support_without_a_server_error(self):
        with patch("builtins.print"):
            response = self.client.post(
                "/support",
                data={
                    "nom": "Test",
                    "email": "test@example.com",
                    "sujet": "Question",
                    "message": "Message de test",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/support")

    def test_support_is_the_only_registered_support_route(self):
        support_rules = [
            rule for rule in self.app.url_map.iter_rules() if rule.rule == "/support"
        ]
        self.assertEqual([rule.endpoint for rule in support_rules], ["support.index"])

    def test_sitemap_contains_the_five_approved_absolute_https_urls(self):
        sitemap = self.client.get("/sitemap.xml")
        root = ElementTree.fromstring(sitemap.data)
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [node.text for node in root.findall("sitemap:url/sitemap:loc", namespace)]
        robots = self.client.get("/robots.txt")

        self.assertEqual(sitemap.status_code, 200)
        self.assertEqual(
            locations,
            [
                f"{PUBLIC_ORIGIN}/",
                f"{PUBLIC_ORIGIN}/privacy",
                f"{PUBLIC_ORIGIN}/cgu",
                f"{PUBLIC_ORIGIN}/mentions-legales",
                f"{PUBLIC_ORIGIN}/support",
            ],
        )
        self.assertTrue(all(url.startswith(PUBLIC_ORIGIN) for url in locations))
        self.assertEqual(robots.status_code, 200)
        self.assertIn(b"Sitemap: https://www.africachangex.com/sitemap.xml", robots.data)

    def test_existing_public_canonicals_are_unchanged(self):
        self.assertEqual(
            CANONICAL_URLS,
            {
                "main.accueil": f"{PUBLIC_ORIGIN}/",
                "legal.privacy": f"{PUBLIC_ORIGIN}/privacy",
                "legal.cgu": f"{PUBLIC_ORIGIN}/cgu",
                "legal.mentions": f"{PUBLIC_ORIGIN}/mentions-legales",
                "support.index": f"{PUBLIC_ORIGIN}/support",
            },
        )


if __name__ == "__main__":
    unittest.main()
