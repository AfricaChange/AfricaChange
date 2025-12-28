from flask import Blueprint, jsonify, session
from services.dashboard_service import AdminDashboardService

admin_realtime = Blueprint(
    "admin_realtime",
    __name__,
    url_prefix="/admin/realtime"
)

@admin_realtime.route("/stats")
def realtime_stats():
    if not session.get("is_admin"):
        return jsonify({"error": "unauthorized"}), 403

    return jsonify(AdminDashboardService.snapshot())
