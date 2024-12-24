from flask import Blueprint, request, jsonify, render_template
import json
import paramiko
from .env import DOCKERFILE_URL, DOCKER_COMPOSE_PLAN_1, DOCKER_COMPOSE_PLAN_2, DOCKER_COMPOSE_PLAN_3
websites = Blueprint('websites', __name__)

@websites.route("/<string:id>", methods=["GET"])
def get_website_info(id):
    print(id)
    with open("app/fake_data/website_info.json", "r") as json_file:
            data = json.load(json_file)
    return jsonify(data), 200


@websites.route("/create", methods=["POST"])
def create_website():
    data = request.get_json()
    print(data)

    # get nova VM info

    # save zipped code somewhere and get url
    hostname = "192.168.1.16"
    port = 22  # Default SSH port
    username = "christopher0612"
    password = "abc123"


    try:
        # Create an SSH client
        ssh_client = paramiko.SSHClient()

        # Automatically add the server's host key (use with caution)
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the server
        ssh_client.connect(hostname=hostname, port=port, username=username, password=password)

        print("Connected to the server.")

        instance_scripts_url = "https://rqrfqewauxwlizbxuekr.supabase.co/storage/v1/object/public/openstack_code/instance-scripts.zip"
        user_code_zip_url = "https://rqrfqewauxwlizbxuekr.supabase.co/storage/v1/object/public/openstack_code/nodejs-app-v3.zip"
        website_id = "abc123"

        # Execute a command on the remote server
        command = "ls -l"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        # command = f"wget -O instance_scripts.zip {instance_scripts_url}"
        # stdin, stdout, stderr = ssh_client.exec_command(command)
        # print(f"Output: {stdout.read().decode()}")
        # print(f"Error: {stderr.read().decode()}")

        # command = "unzip instance_scripts.zip"
        # stdin, stdout, stderr = ssh_client.exec_command(command)
        # print(f"Output: {stdout.read().decode()}")
        # print(f"Error: {stderr.read().decode()}")

        command = f"source setup-website-folder.sh '{website_id}' '{user_code_zip_url}' '{DOCKERFILE_URL}' '{DOCKER_COMPOSE_PLAN_3}'"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        command = f"source start-website.sh '{website_id}'"
        stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        # Retrieve command output

    except paramiko.SSHException as e:
        print(f"SSH connection error: {e}")

    return jsonify({"status": "success", "data": "Nothing"}), 200
