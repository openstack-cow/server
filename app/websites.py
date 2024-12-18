from flask import Blueprint, request, jsonify, render_template
from .models import Website, CinderVolume, NovaVM, User, Plan
import json
from .utils.token_required import token_required
from .utils.openstack_api import get_openstack_connection
from . import db
websites = Blueprint('websites', __name__)
conn=get_openstack_connection()
@websites.route("/test", methods=["GET"])
def test():
        users = User.query.all()  # Fetch all users
        # Serialize the query results into a list of dictionaries
        users_data = [{"id": user.id, "email": user.email, "name": user.name} for user in users]
        return jsonify({"data": users_data})  # Return serialized data
@websites.route("/<int:id>", methods=["GET"])
def get_website_info(id):
    print(id)
    with open("app/fake_data/website_info.json", "r") as json_file:
            data = json.load(json_file)
    return jsonify(data), 200
@websites.route("/",methods=["GET"])
@token_required
def get_all_website_info(): 
        all_websites = Website.query.all()
        websites_info = []
        for website in all_websites:
            websites_info.append(get_website_detail(website.id))
        return jsonify({"data": websites_info}), 200
@websites.route("/<int:id>", methods=["GET"])
@token_required
def get_website_info_detail( id):
        website_info=get_website_detail(id)
        return jsonify({"data":website_info}), 200       
@websites.route("/<int:id>",methods=["DELETE"])
@token_required
def delete_website(id):
        try:
                website = Website.query.filter_by(id=id).first()

                if not website:
                        return jsonify({"error": "Website not found"}), 404

                db.session.delete(website)
                db.session.commit()

                return jsonify({"message": f"Website with ID {id} has been deleted successfully"}), 200

        except Exception as e:
                db.session.rollback()
                return jsonify({"error": str(e)}), 500

@websites.route("/<int:id>/stauts", methods=["POST"])
@token_required
def update_website_status(id):
        try:
                data = request.get_json()
                action = data.get("action")

                valid_actions = {"start", "stop", "restart", "reset"}
                if action not in valid_actions:
                        return jsonify({"error": f"Invalid action. Valid actions are: {', '.join(valid_actions)}"}), 400

                website = Website.query.filter_by(id=id).first()
                if not website:
                        return jsonify({"error": "Website not found"}), 404

                if action == "start":
                        website.status = "running"
                elif action == "stop":
                        website.status = "stopped"
                elif action == "restart":
                        website.status = "restarting"
                elif action == "reset":
                        website.status = "resetting"

                db.session.commit()

                return jsonify({
                        "message": f"Action '{action}' performed successfully.",
                        "website_id": website.id,
                        "new_status": website.status
                }), 200

        except Exception as e:
                db.session.rollback()  
                return jsonify({"error": str(e)}), 500
        

def get_website_detail(id):
        website_data=Website.query.filter_by(id=id)
        if not website_data:
                return jsonify({"error": "Website not found"}), 404
        plan_data = Plan.query.filter_by(id=website_data.plan_id).first()
        if plan_data.has_mysql:
                mysql_details = {
                        "mysql_host": "localhost",  
                        "mysql_port": 3306,         
                        "mysql_user": "root",       
                        "mysql_password": "password",
                        "mysql_database": "abc"
                }
        if plan_data.has_redis:
                redis_url = f"redis://localhost:6379/abc"  

        plan = {
                "id": plan_data.id,
                "storage_in_gb": plan_data.storage_in_gb, 
                "name": plan_data.name,
                "price": plan_data.price
        } if plan_data else None
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

def get_nova_detail(id):
        novaVm=conn.compute.get_server(id)
        if not novaVm:
                return jsonify({"error": "Nova VM not found"}), 404
        vm_info= {
                "vm_id":novaVm.id,
        }
def get_cinder_detail(id):
        return
