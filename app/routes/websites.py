from flask import Blueprint, request, jsonify
from app.models import Website, Plan, User
from ..utils.token_required import token_required # type: ignore
websites = Blueprint('websites', __name__)

from typing import Any

@websites.route("", methods=["GET"])
@token_required
def get_all_websites(current_user: User):
    all_websites: list[Website] = Website.query.all()
    websites_info: list[dict[str, Any]] = []
    for website in all_websites:
        websites_info.append(get_website_detail(website.id))
    return jsonify(websites_info), 200

@websites.route("", methods=["POST"])
@token_required
def create_website(current_user: User):
    body = request.get_json()
    name = body.get("name")
    plan_id = body.get("plan_id")
    build_script = body.get("build_script")
    start_script = body.get("start_script")
    user_code_zip_url = body.get("user_code_zip_url")
    port = body.get("port")
    if not all([name, plan_id, build_script, start_script, user_code_zip_url, port]):
        return jsonify({"error": "Missing required fields"}), 400
    from app.utils.websites import create_new_website
    new_website = create_new_website(name, int(plan_id), current_user.id, build_script, start_script, user_code_zip_url, int(port))
    return get_website_detail(new_website.id), 200

@websites.route("/<int:id>", methods=["GET"])
@token_required
def get_website_info_detail(current_user: User, id: int):
    website_info = get_website_detail(int(id))
    return jsonify(website_info), 200

@websites.route("/<int:id>/status", methods=["PUT"])
@token_required
def update_website_status_api(current_user: User, id: int):
    body = request.get_json()
    action = body.get("action")
    if action != "start" and action != "stop" and action != "restart":
        return jsonify({"error": "Invalid action"}), 400
    from app.utils.websites import update_website_status
    update_website_status(action, int(id))
    return jsonify({}), 200

@websites.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_website_api(current_user: User, id: int):
    from app.utils.websites import delete_website
    delete_website(int(id))
    return jsonify({}), 200

def get_website_detail(id: int) -> dict[str, Any]:
    from app.env import PUBLIC_IP_ADDRESS
    from app.routes.plans import plan_schema
    website_data: Website|None = Website.query.get(id)
    if not website_data:
        raise ValueError(f"Website with ID {id} not found in database.")
    
    plan_entry: Plan|None = Plan.query.get(website_data.plan_id)
    if plan_entry is None:
        raise ValueError(f"Plan with ID {website_data.plan_id} not found in database.")

    website_details: dict[str, Any] = {
        "id": website_data.id,
        "name": website_data.name,
        "plan_id": website_data.plan_id,
        "status": website_data.status,
        "message": website_data.message,
        "address": f"http://{PUBLIC_IP_ADDRESS}:{website_data.public_port}" if website_data.status == "ACTIVE" and website_data.public_port else "Unknown",
        "created_at": website_data.created_at,
        "plan": plan_schema.dump(plan_entry),
        "openstack_nova_vm_id": website_data.nova_vm.openstack_nova_vm_id,
        "openstack_nova_vm_floating_ip": website_data.nova_vm.floating_ip,
    }

    return website_details
