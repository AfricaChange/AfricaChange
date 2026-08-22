import os
import unittest

from flask import Flask

from database import db
from models import Rate
from routes.convert import convert
from routes.main import main


class HomepageRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(
            __name__,
            template_folder=os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "templates",
            ),
            static_folder=os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "static",
            ),
        )
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY="test-secret",
            WTF_CSRF_ENABLED=False,
            SERVER_NAME="localhost",
        )
        db.init_app(self.app)
        self.app.register_blueprint(main)
        self.app.register_blueprint(convert)

        @self.app.context_processor
        def inject_globals():
            return {"csrf_token": lambda: "test-csrf"}

        def endpoint_response(label):
            def _view():
                return label

            return _view

        self.app.add_url_rule("/connexion", endpoint="auth.connexion", view_func=endpoint_response("connexion"))
        self.app.add_url_rule("/inscription", endpoint="auth.inscription", view_func=endpoint_response("inscription"))
        self.app.add_url_rule("/tableau-de-bord", endpoint="auth.tableau_de_bord", view_func=endpoint_response("dashboard"))
        self.app.add_url_rule("/deconnexion", endpoint="auth.deconnexion", view_func=endpoint_response("deconnexion"))
        self.app.add_url_rule("/support", endpoint="support.index", view_func=endpoint_response("support"))
        self.app.add_url_rule("/admin", endpoint="admin.dashboard", view_func=endpoint_response("admin"))

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        db.session.add_all(
            [
                Rate(from_currency="XOF", to_currency="GNF", rate=14.0),
                Rate(from_currency="GNF", to_currency="XOF", rate=0.065),
                Rate(from_currency="EUR", to_currency="XOF", rate=655.43),
                Rate(from_currency="XOF", to_currency="EUR", rate=0.0015),
            ]
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_homepage_loads_with_transactional_converter(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Envoyez. Convertissez. Recevez.".encode("utf-8"), response.data)
        self.assertIn(b'id="home-converter"', response.data)
        self.assertIn(b'id="sourceCurrency"', response.data)
        self.assertIn(b'id="targetCurrency"', response.data)
        self.assertIn("Continuer".encode("utf-8"), response.data)
        self.assertIn("1 XOF = 14.0 GNF".encode("utf-8"), response.data)

    def test_homepage_uses_real_initial_corridor_rate(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"from_currency": "XOF"', response.data)
        self.assertIn(b'"to_currency": "GNF"', response.data)
        self.assertIn(b'"rate": 14.0', response.data)

    def test_quote_api_returns_dynamic_rate_for_supported_corridor(self):
        response = self.client.post(
            "/convert/api/convertir",
            json={
                "montant": 5000,
                "from_currency": "XOF",
                "to_currency": "GNF",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["corridor"], "XOF->GNF")
        self.assertEqual(payload["taux"], 14.0)
        self.assertEqual(payload["montant_converti"], 70000.0)
        self.assertEqual(payload["from_country_code"], "SN")
        self.assertEqual(payload["to_country_code"], "GN")
        self.assertFalse(payload["frais_connus"])

    def test_quote_api_reacts_to_source_change(self):
        response = self.client.post(
            "/convert/api/convertir",
            json={
                "montant": 100,
                "from_currency": "EUR",
                "to_currency": "XOF",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["corridor"], "EUR->XOF")
        self.assertEqual(payload["taux"], 655.43)
        self.assertEqual(payload["montant_converti"], 65543.0)

    def test_quote_api_reacts_to_destination_change(self):
        response = self.client.post(
            "/convert/api/convertir",
            json={
                "montant": 5000,
                "from_currency": "XOF",
                "to_currency": "EUR",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["corridor"], "XOF->EUR")
        self.assertEqual(payload["taux"], 0.0015)
        self.assertEqual(payload["montant_converti"], 7.5)

    def test_quote_api_uses_real_inverse_corridor_not_reciprocal_guess(self):
        response = self.client.post(
            "/convert/api/convertir",
            json={
                "montant": 70000,
                "from_currency": "GNF",
                "to_currency": "XOF",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["corridor"], "GNF->XOF")
        self.assertEqual(payload["taux"], 0.065)
        self.assertEqual(payload["montant_converti"], 4550.0)

    def test_quote_api_recalculates_amount_when_amount_changes(self):
        response = self.client.post(
            "/convert/api/convertir",
            json={
                "montant": 10000,
                "from_currency": "XOF",
                "to_currency": "GNF",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["montant_converti"], 140000.0)

    def test_quote_api_returns_corridor_unavailable_error(self):
        response = self.client.post(
            "/convert/api/convertir",
            json={
                "montant": 5000,
                "from_currency": "XOF",
                "to_currency": "USD",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"error": "Ce corridor n'est pas encore disponible."},
        )

    def test_homepage_redirects_to_existing_conversion_workflow(self):
        response = self.client.post(
            "/demarrer-conversion",
            data={
                "montant": "5000",
                "from_currency": "XOF",
                "to_currency": "GNF",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "/convert/?montant=5000&from_currency=XOF&to_currency=GNF",
            response.headers["Location"],
        )

    def test_homepage_continue_preserves_changed_pair(self):
        response = self.client.post(
            "/demarrer-conversion",
            data={
                "montant": "100",
                "from_currency": "EUR",
                "to_currency": "XOF",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            "/convert/?montant=100&from_currency=EUR&to_currency=XOF",
            response.headers["Location"],
        )

    def test_homepage_falls_back_when_rates_are_unavailable(self):
        Rate.query.delete()
        db.session.commit()

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'"error_code": "rates_unavailable"', response.data)
        self.assertIn("Calcul du taux...".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
