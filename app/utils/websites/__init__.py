from typing import Literal
from ...models import Website, NovaVM, Plan
from app.utils.ssh import create_ssh_client_to_nova_vm, quick_shell_to_nova_vm
from app.utils.openstack_api import get_openstack_connection
import time

WebsiteUpdateAction = Literal['start', 'stop', 'restart']

def create_new_website_in_docker(
    name: str, plan_id: int, user_id: int,
    user_code_zip_url: str, nova_vm_port: int,
):
    # Get plan from db
    plan = Plan.query.get(plan_id)
    if not plan:
        raise ValueError(f"No plan found with id {plan_id}")
    
    from .choose_plan import select_or_create_nova_instance

    nova_vm_entry = select_or_create_nova_instance(plan_id)

    nova_floating_ip = nova_vm_entry.floating_ip
    openstack_nova_vm_id = nova_vm_entry.openstack_nova_vm_id

    openstack = get_openstack_connection()
    openstack_nova_vm = openstack.compute.get_server(openstack_nova_vm_id) # type: ignore
    openstack.compute.wait_for_server(openstack_nova_vm) # type: ignore
    
    ssh_client = create_ssh_client_to_nova_vm(nova_floating_ip)
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

def update_website_status(action: WebsiteUpdateAction, id: int):
    from app import db
    valid_actions = {"start", "stop", "restart"}
    if action not in valid_actions:
        raise ValueError(f"Invalid action '{action}'. Valid actions are: {valid_actions}")

    # Determine Nova VM
    nova_vm: NovaVM = Website.join(NovaVM, Website.nova_vm_id == NovaVM.id).filter( # type: ignore
        Website.id == id
    ).first() # type: ignore

    if nova_vm is None:
        raise ValueError(f"No website found with id {id}")

    nova_floating_ip: str = str(nova_vm.floating_ip) # type: ignore
    
    # Determine website
    website = Website.query.filter_by( # type: ignore
        id=id
    ).first()
    if not website:
        raise ValueError(f"No website found with id {id}")

    cmd = f"docker {action} nodejs-app-{id}"

    try:
        if action == "start":
            website.status = "Starting"
        elif action == "stop":
            website.status = "Stopping"
        elif action == "restart":
            website.status = "Restarting"

        db.session.commit()

        quick_shell_to_nova_vm(nova_floating_ip, cmd)
    except:
        db.session.rollback()
        raise
