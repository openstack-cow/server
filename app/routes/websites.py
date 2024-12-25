from flask import Blueprint, request, jsonify
from app.models import Website, Plan
from ..utils.token_required import token_required # type: ignore
websites = Blueprint('websites', __name__)

from typing import Any

def get_website_detail(id: int) -> dict[str, Any]:
    website_data: Website|None = Website.query.get(id)
    if not website_data:
        raise ValueError(f"Website with ID {id} not found in database.")
    
    plan_entry: Plan|None = Plan.query.get(website_data.plan_id)
    if plan_entry is None:
        raise ValueError(f"Plan with ID {website_data.plan_id} not found in database.")

    plan: dict[str, Any] = {
        "id": plan_entry.id,
        "storage_in_mb": plan_entry.storage_in_mb,
        "name": plan_entry.name,
        "monthly_fee_in_usd": plan_entry.monthly_fee_in_usd,
    }
    website_details: dict[str, Any] = {
        "id": website_data.id,
        "name": website_data.name,
        "plan_id": website_data.plan_id,
        "status": website_data.status,
        "address": f"http://{website_data.public_port}",
        "plan": plan,
    }
    if plan_entry.has_mysql:
        website_details.update({
            "mysql_host": "localhost",
            "mysql_port": 3306,
            "mysql_user": "root",
            "mysql_password": "root",
            "mysql_database": "my_database"
        })
    if plan_entry.has_redis:
        website_details.update({
            "redis_url": f"redis://localhost:6379"
        })

    return website_details

@websites.route("/", methods=["GET"])
@token_required
def get_all_websites():
    all_websites: list[Website] = Website.query.all()
    websites_info: list[dict[str, Any]] = []
    for website in all_websites:
        websites_info.append(get_website_detail(website.id))
    return jsonify(websites_info), 200

@websites.route("/<int:id>", methods=["GET"])
@token_required
def get_website_info_detail(id: str):
    website_info = get_website_detail(int(id))
    return jsonify(website_info), 200

@websites.route("/<int:id>/status", methods=["PUT"])
@token_required
def update_website_status_api(id: str):
    body = request.get_json()
    action = body.get("action")
    if action != "start" and action != "stop" and action != "restart":
        return jsonify({"error": "Invalid action"}), 400
    from app.utils.websites import update_website_status
    update_website_status(action, int(id))
    return jsonify({}), 200

@websites.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_website_api(id: str):
    from app.utils.websites import delete_website
    delete_website(int(id))
    return jsonify({}), 200
