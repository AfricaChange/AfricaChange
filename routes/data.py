from flask import Blueprint, render_template

data_bp = Blueprint('data', __name__)

@data_bp.route('/delete-data')
def delete_data():
    return render_template('delete_data.html')