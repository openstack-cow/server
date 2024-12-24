from flask import Blueprint, request, jsonify, render_template
import paramiko
from .models import Website, NovaVM, User, Plan
import json
from .utils.token_required import token_required
from .utils.openstack_api import get_openstack_connection
from . import db
from .env import NOVA_VM_PRIVATE_KEY_PATH
import paramiko
from .env import DOCKERFILE_URL, DOCKER_COMPOSE_PLAN_1, DOCKER_COMPOSE_PLAN_2, DOCKER_COMPOSE_PLAN_3
websites = Blueprint('websites', __name__)
conn = get_openstack_connection()


@websites.route("/test", methods=["GET"])
def test():
    users = User.query.all()  # Fetch all users
    # Serialize the query results into a list of dictionaries
    users_data = [{"id": user.id, "email": user.email,
                   "name": user.name} for user in users]
    return jsonify({"data": users_data})  # Return serialized data


@websites.route("/<int:id>", methods=["GET"])
def get_website_info(id):
    print(id)
    with open("app/fake_data/website_info.json", "r") as json_file:
        data = json.load(json_file)
    return jsonify(data), 200


@websites.route("/", methods=["GET"])
@token_required
def get_all_website_info():
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


@websites.route("/<int:id>/stauts", methods=["POST"])
@token_required
def update_website_status(id):
    try:
        data = request.get_json()
        action = data.get("action")
        action_shell= f"docker {action} nodejs-app-{id}"
        valid_actions = {"start", "stop", "restart"}
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

        nova_vm_shell(action_shell, id)
        
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
    website_data = Website.query.filter_by(id=id)
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
        "storage_in_mb": plan_data.storage_in_mb,
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


def nova_vm_shell(action, website_id):
    nova_floating_ip = Website.join(NovaVM, Website.nova_vm_id == NovaVM.id).filter(
        Website.id == website_id).first().floating_ip
    nova_name = "ubuntu"
    port = 22
    private_key_path = NOVA_VM_PRIVATE_KEY_PATH  

    try:
        private_key = paramiko.Ed25519Key.from_private_key_file(private_key_path)

        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())  

        ssh_client.connect(nova_floating_ip, port, username=nova_name, pkey=private_key)
        print("Connected to the server")

        stdin, stdout, stderr = ssh_client.exec_command(action)

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            print(f"Command Output:\n{output}")
        if error:
            print(f"Command Error:\n{error}")

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        ssh_client.close()
        print("Connection closed")


def create_ssh_client(website_id):
    # nova_floating_ip = Website.join(NovaVM, Website.nova_vm_id == NovaVM.id).filter(Website.id == website_id).first().floating_ip
    
    # remove this hardcode value
    nova_floating_ip = "172.16.2.221"
    nova_name = "ubuntu"
    port = 22
    private_key_path = NOVA_VM_PRIVATE_KEY_PATH  

    try:
        private_key = paramiko.Ed25519Key.from_private_key_file(private_key_path)

        # Create an SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())  

        ssh_client.connect(nova_floating_ip, port, username=nova_name, pkey=private_key)
        print("Connected to the server")

        return ssh_client
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

@websites.route("/create", methods=["POST"])
def create_website():
    try:
        data = request.get_json()
        print(data)

        website_name = data.get("name")
        plan_id = data.get("plan_id")
        user_id = data.get("user_id")
        user_code_zip_url = data.get("user_code_zip_url")
        nova_vm_port = data.get("app_port")

        if plan_id == 1:
            DOCKER_COMPOSE_PLAN_URL = DOCKER_COMPOSE_PLAN_1
            USE_CASE = "nodejs"
        elif plan_id == 2:
            DOCKER_COMPOSE_PLAN_URL = DOCKER_COMPOSE_PLAN_2
            USE_CASE = "nodejs_mysql"
        elif plan_id == 3:
            DOCKER_COMPOSE_PLAN_URL = DOCKER_COMPOSE_PLAN_3
            USE_CASE = "nodejs_mysql_redis"
        else:
            return jsonify({"error": "Invalid plan ID"}), 400

        # scripts to setup
        instance_scripts_url = "https://rqrfqewauxwlizbxuekr.supabase.co/storage/v1/object/public/openstack_code/instance-scripts.zip"

        # remove this hardcode value
        website_id = "abc123"
        
        ssh_client = create_ssh_client(website_id)
        if not ssh_client:
            return jsonify({"error": "Failed to connect to Nova instance"}), 500
        

        # Execute a command on the remote server
        command = "ls -l"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")


        # check if instance already has the scripts
        command = f"test -f instance-scripts.zip && echo 'exist' || echo 'missing'"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode().strip()
        if output == "missing":
            command = f"wget -O instance-scripts.zip {instance_scripts_url}"
            stdin, stdout, stderr = ssh_client.exec_command(command)
            print(f"Output: {stdout.read().decode()}")
            print(f"Error: {stderr.read().decode()}")

            command = "unzip instance-scripts.zip"
            stdin, stdout, stderr = ssh_client.exec_command(command)
            print(f"Output: {stdout.read().decode()}")
            print(f"Error: {stderr.read().decode()}")
        

         # check if Docker is installed
        command = "docker --version"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode().strip()
        if not output:
            command = "source setup-instance.sh"
            stdin, stdout, stderr = ssh_client.exec_command(command)
            print(f"Output: {stdout.read().decode()}")
            print(f"Error: {stderr.read().decode()}")
        

        command = f"source setup-website-folder.sh '{website_id}' '{user_code_zip_url}' '{DOCKERFILE_URL}' '{DOCKER_COMPOSE_PLAN_URL}'"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        command = f"source setup-env.sh './{website_id}' '{USE_CASE}' '{nova_vm_port}' '{website_id}'"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        command = f"source run-website.sh '{website_id}'"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        # Retrieve command output

    except paramiko.SSHException as e:
        print(f"SSH connection error: {e}")
    finally:
        ssh_client.close()
        print("Connection closed")

    return jsonify({"status": "success", "data": "Nothing"}), 200
