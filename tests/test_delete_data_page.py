import os
import unittest

from flask import Flask

from routes.data import data_bp


class DeleteDataPageTestCase(unittest.TestCase):
    def setUp(self):
        root = os.path.dirname(os.path.dirname(__file__))
        self.app = Flask(__name__, template_folder=os.path.join(root, "templates"))
        self.app.config.update(TESTING=True, SECRET_KEY="delete-data-test-secret")
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
            ("/support", "support.index"),
            ("/faq", "support.faq"),
        ):
            self.app.add_url_rule(rule, endpoint=endpoint, view_func=placeholder)

        self.app.register_blueprint(data_bp)
        self.client = self.app.test_client()

    def test_delete_data_page_is_public_and_contains_the_required_instructions(self):
        response = self.client.get("/delete-data")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"support@africachangex.com", response.data)
        self.assertIn(b"Demander la suppression de vos donn", response.data)
        self.assertIn(b"v\xc3\xa9rification d'identit", response.data)
        self.assertIn(b"obligation l\xc3\xa9gale", response.data)
        self.assertIn(b'href="/privacy"', response.data)
        self.assertIn(b'href="/cgu"', response.data)
        self.assertNotIn(b"72 heures", response.data)

    def test_delete_data_page_remains_an_instruction_page(self):
        response = self.client.post("/delete-data")

        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()
