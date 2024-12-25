from typing import Literal
from ..models import Website, NovaVM, Plan
from app.env import NOVA_VM_PRIVATE_KEY_PATH
import paramiko

def create_ssh_client(floating_ip: str):
    ssh_client = paramiko.SSHClient()
    private_key = paramiko.Ed25519Key.from_private_key_file(NOVA_VM_PRIVATE_KEY_PATH)

    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(floating_ip, port=22, username="ubuntu", pkey=private_key, timeout=120)
    print(f"Connected to the server at {floating_ip}")

    return ssh_client

WebsiteUpdateAction = Literal['start', 'stop', 'restart']

def website_action(action: WebsiteUpdateAction, website_id: int):
    """
    Execute action on the Nova VM instance containing the website.
    """
    result = Website.join(NovaVM, Website.nova_vm_id == NovaVM.id).filter( # type: ignore
        Website.id == website_id
    ).first() # type: ignore

    if result is None:
        raise ValueError(f"No website found with id {website_id}")

    nova_floating_ip: str = str(result.floating_ip) # type: ignore

    ssh_client = create_ssh_client(nova_floating_ip)
    try:
        _stdin, stdout, stderr = ssh_client.exec_command(action)

        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if output:
            print(f"Command Output:\n{output}")
        if error:
            print(f"Command Error:\n{error}")

    finally:
        ssh_client.close()
        print("Connection closed")

def create_website(
    name: str, plan_id: int, user_id: int,
    user_code_zip_url: str, nova_vm_port: int,
):
    # Get plan from db
    plan = Plan.query.get(plan_id)
    if not plan:
        raise ValueError(f"No plan found with id {plan_id}")
    
    try:
        # Execute a command on the remote server
        command = "ls -l"
        _stdin, stdout, stderr = ssh_client.exec_command(command)
        print(f"Output: {stdout.read().decode()}")
        print(f"Error: {stderr.read().decode()}")

        # check if instance already has the scripts
        command = f"test -f instance-scripts.zip && echo 'exist' || echo 'missing'"
        _stdin, stdout, stderr = ssh_client.exec_command(command)
        output = stdout.read().decode().strip()
        if output == "missing":
            command = f"wget -O instance-scripts.zip {user_code_zip_url}"
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

