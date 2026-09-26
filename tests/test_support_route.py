import os
import unittest
from unittest.mock import patch

from flask import Flask

from routes.seo import seo
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

    def test_seo_endpoints_remain_available(self):
        sitemap = self.client.get("/sitemap.xml")
        robots = self.client.get("/robots.txt")
        self.assertEqual(sitemap.status_code, 200)
        self.assertIn(b"https://www.africachangex.com/privacy", sitemap.data)
        self.assertEqual(robots.status_code, 200)
        self.assertIn(b"Sitemap: https://www.africachangex.com/sitemap.xml", robots.data)


if __name__ == "__main__":
    unittest.main()
