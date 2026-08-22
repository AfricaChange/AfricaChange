import unittest

from flask import Flask

from app_bootstrap.hooks import register_request_hooks
from app_bootstrap.security import configure_runtime_security, register_template_globals


class RuntimeSecurityTests(unittest.TestCase):
    def create_app(self, *, is_production: bool) -> Flask:
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            SECRET_KEY="test-secret",
            WTF_CSRF_ENABLED=False,
            IS_PRODUCTION=is_production,
            SESSION_COOKIE_SECURE=is_production,
        )
        register_template_globals(app)
        register_request_hooks(app)
        configure_runtime_security(app)

        @app.route("/")
        def home():
            return "ok"

        return app

    def test_development_allows_http_for_localhost(self):
        app = self.create_app(is_production=False)

        with app.test_client() as client:
            response = client.get(
                "/",
                base_url="http://localhost",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"ok")

    def test_production_redirects_http_to_https(self):
        app = self.create_app(is_production=True)

        with app.test_client() as client:
            response = client.get(
                "/",
                base_url="http://africachangex.test",
                follow_redirects=False,
            )

        self.assertEqual(response.status_code, 301)
        self.assertTrue(
            response.headers["Location"].startswith("https://"),
            response.headers["Location"],
        )


if __name__ == "__main__":
    unittest.main()
