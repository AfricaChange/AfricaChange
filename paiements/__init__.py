from flask import Blueprint

paiements_bp = Blueprint(
    'paiements',
    __name__,
    template_folder='templates'
)