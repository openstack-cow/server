from flask import Blueprint, request, jsonify, render_template
import paramiko
from ..models import Website, NovaVM, User, Plan
import json
from ..utils.token_required import token_required
from ..utils.openstack_api import get_openstack_connection
from .. import db
from ..env import NOVA_VM_PRIVATE_KEY_PATH
from ..env import DOCKERFILE_URL, DOCKER_COMPOSE_PLAN_1, DOCKER_COMPOSE_PLAN_2, DOCKER_COMPOSE_PLAN_3
websites = Blueprint('websites', __name__)

def get_website_detail(id: int):
    website_data = Website.query.filter_by(id=id)
    if not website_data:
        raise ValueError(f"Website with ID {id} not found in database.")
    
    plan_data = Plan.query.filter_by(id=website_data.plan_id).first()
    if plan_data is None:
        raise ValueError(f"Plan with ID {website_data.plan_id} not found in database.")

    if plan_data.has_mysql:
        mysql_details = {
            "mysql_host": "localhost",
            "mysql_port": 3306,
            "mysql_user": "root",
            "mysql_password": "root",
            "mysql_database": "database"
        }
    if plan_data.has_redis:
        redis_url = f"redis://localhost:6379"

    plan = {
        "id": plan_data.id,
        "storage_in_mb": plan_data.storage_in_mb,
        "name": plan_data.name,
        "price": plan_data.price
    }
    website_details = {
        "id": website_data.id,
        "name": website_data.name,
        "plan_id": website_data.plan_id,
        "status": website_data.status,
        "address": f"http://{website_data.public_port}",
        "plan": plan,
        "redis_url": redis_url,
        "mysql": mysql_details
    }
    return jsonify(website_details), 200

@websites.route("/test", methods=["GET"])
def test():
    users = User.query.all()  # Fetch all users
    # Serialize the query results into a list of dictionaries
    users_data = [{"id": user.id, "email": user.email,
                   "name": user.name} for user in users]
    return jsonify({"data": users_data})  # Return serialized data

@websites.route("/", methods=["GET"])
@token_required
def get_all_websites():
    all_websites = Website.query.all()
    websites_info = []
    for website in all_websites:
        websites_info.append(get_website_detail(website.id))
    return jsonify({"data": websites_info}), 200

@websites.route("/<int:id>", methods=["GET"])
@token_required
def get_website_info_detail(id):
    website_info = get_website_detail(id)
    return jsonify({"data": website_info}), 200


@websites.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_website(id):
    try:
        website = Website.query.filter_by(id=id).first()
        docker_compose_path= f"/home/ubuntu/web_{id}/"
        action =f"cd {docker_compose_path} && docker-compose down -v"
        nova_vm_shell(action, id)
        if not website:
            return jsonify({"error": "Website not found"}), 404

        db.session.delete(website)
        db.session.commit()

        return jsonify({"message": f"Website with ID {id} has been deleted successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
