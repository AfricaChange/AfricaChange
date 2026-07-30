from flask import render_template
from flask_wtf.csrf import CSRFError


def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("500.html"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        return render_template("csrf_error.html", reason=error.description), 400
