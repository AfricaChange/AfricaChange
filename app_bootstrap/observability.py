import logging
import os


def configure_logging(app):
    if app.debug:
        return

    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    log_dir = os.path.abspath(log_dir)
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "africachange_errors.log")
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    app.logger.addHandler(handler)
