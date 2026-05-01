# routes/legal.py

from flask import Blueprint, render_template

legal = Blueprint('legal', __name__)

@legal.route('/privacy')
def privacy():
    return render_template('legal/privacy.html')

@legal.route('/cgu')
def cgu():
    return render_template('legal/cgu.html')

@legal.route('/mentions-legales')
def mentions():
    return render_template('legal/mentions.html')