import time
from sqlalchemy.exc import SQLAlchemyError
from ...models import db, NovaVM, Plan
from ..openstack_api import get_openstack_connection
from ...env import (
    NOVA_VM_FLAVOR_ID, NOVA_VM_IMAGE_ID, NOVA_VM_NETWORK_ID,
    NOVA_VM_SECURITY_GROUP_NAME, NOVA_VM_KEYPAIR_NAME,
    NOVA_VM_EXTERNAL_NETWORK_ID
)

from typing import Any, TypedDict

class NovaVMResourceStats(TypedDict):
    cpu_cores: int
    ram_in_mb: int
    storage_in_mb: int

class NovaVMSelectionResult(TypedDict):
    nova_instance: Any
    remaining_resources: NovaVMResourceStats

def get_total_resources_from_flavor() -> dict[str, int]:
    """Get total resources of the Nova Instance using the flavor ID from OpenStack."""
    try:
        conn = get_openstack_connection()
        flavor = conn.compute.get_flavor(NOVA_VM_FLAVOR_ID) # type: ignore
        if not flavor:
            raise ValueError(f"Flavor with ID {NOVA_VM_FLAVOR_ID} not found.")

        return {
            "cpu_cores": 2 * flavor.vcpus, # type: ignore
            "ram_in_mb": flavor.ram, # type: ignore
            "storage_in_mb": flavor.disk*1024  # Convert GB to MB # type: ignore
        }

    except Exception as e:
        raise RuntimeError(f"Failed to fetch flavor details: {str(e)}")

from typing import Optional

def calculate_nova_instance_stats(nova_vm_id: int) -> NovaVMSelectionResult:
    """Thống kê tài nguyên đã sử dụng và còn lại trong một Nova Instance."""
    try:
        nova_instance: Optional[NovaVM] = NovaVM.query.filter_by(id=nova_vm_id).first() # type: ignore
        if not nova_instance:
            raise ValueError(f"Nova Instance with ID {nova_vm_id} not found.")

        total_resources = get_total_resources_from_flavor()

        print(total_resources)

        websites = nova_instance.websites  # Assume a relationship is defined # type: ignore
        used_resources = {
            "cpu_cores": sum(website.plan.cpu_cores for website in websites), # type: ignore
            "ram_in_mb": sum(website.plan.ram_in_mb for website in websites), # type: ignore
            "storage_in_mb": sum(website.plan.storage_in_mb for website in websites) # type: ignore
        }

        print(used_resources)

        remaining_resources: NovaVMResourceStats = {
            "cpu_cores": total_resources["cpu_cores"] - used_resources["cpu_cores"],
            "ram_in_mb": total_resources["ram_in_mb"] - used_resources["ram_in_mb"],
            "storage_in_mb": total_resources["storage_in_mb"] - used_resources["storage_in_mb"]
        }
        print(remaining_resources)

        x: Any = nova_instance

        return {
            "nova_instance": x,
            "remaining_resources": remaining_resources
        }

    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")
    
def select_or_create_nova_instance(plan_id: int) -> NovaVM:
    plan = Plan.query.filter_by(id=plan_id).first() # type: ignore
    if not plan:
        raise ValueError("Plan not found.")

    nova_instances = NovaVM.query.filter(NovaVM.status.in_(["ACTIVE", "CREATING"])).all() # type: ignore

    for nova_instance in nova_instances: # type: ignore
        stats = calculate_nova_instance_stats(nova_instance.id) # type: ignore
        if stats and all(
            stats["remaining_resources"][key] >= getattr(plan, key) # type: ignore
            for key in ["cpu_cores", "ram_in_mb", "storage_in_mb"]
        ):
            return nova_instance # type: ignore

    return create_new_nova_instance()

def create_new_nova_instance():
    conn = get_openstack_connection()

    nova_vm_entry = NovaVM(
        status="CREATING", # type: ignore
        floating_ip="(Unknown)", # type: ignore
        openstack_nova_vm_id="(Unknown)" # type: ignore
    )
    db.session.add(nova_vm_entry)
    db.session.commit()

    nova_vm = conn.compute.create_server( # type: ignore
        name="new-nova-instance" + str(nova_vm_entry.id),
        flavorRef=NOVA_VM_FLAVOR_ID,
        imageRef=NOVA_VM_IMAGE_ID,
        networks=[{"uuid": NOVA_VM_NETWORK_ID}],
        security_groups=[{ "name": NOVA_VM_SECURITY_GROUP_NAME }],
        key_name=NOVA_VM_KEYPAIR_NAME
    )
    nova_vm = conn.compute.wait_for_server(nova_vm) # type: ignore

    # Get the port ID associated with the instance
    ports = list(conn.network.ports(device_id=nova_vm.id))  # type: ignore
    if not ports:
        raise RuntimeError(f"No ports found for instance {nova_vm.id}") # type: ignore
    port_id = ports[0].id  # Assuming the first port is the one we want # type: ignore

    # Create and attach Floating IP to the specific port
    floating_ip = conn.network.create_ip(floating_network_id=NOVA_VM_EXTERNAL_NETWORK_ID) # type: ignore
    conn.network.update_ip(floating_ip, port_id=port_id) # type: ignore

    # Run SSH command to check if the connection is successful
    from app.utils.ssh import create_ssh_client_to_nova_vm, execute_command
    ssh_client = None
    while True:
        try:
            ssh_client = create_ssh_client_to_nova_vm(nova_vm_entry.floating_ip)
            break
        except:
            print("SSH connection failed. Retrying...")
            time.sleep(5)
            continue
    
    # Setup new Nova VM with necessary commands
    try:
        # Setup DNS first and foremost!
        execute_command(ssh_client, "PRIMARY_INTERFACE=$(ip route | awk '/default/ {print $5; exit}')")
        execute_command(ssh_client, "sudo resolvectl dns ${PRIMARY_INTERFACE} 8.8.8.8")
        execute_command(ssh_client, "ping -c 4 supabase.co")
        execute_command(ssh_client, "sudo apt update")
        execute_command(ssh_client, "sudo apt install -y bash wget unzip")
        execute_command(ssh_client, "wget -O setup_nova_vm.sh https://iweptimpblcxlwztoziq.supabase.co/storage/v1/object/public/iaas/scripts/setup_nova_vm.sh")
        execute_command(ssh_client, "chmod +x setup_nova_vm.sh")
        execute_command(ssh_client, "bash setup_nova_vm.sh")
    finally:
        ssh_client.close()

    # Update the NovaVM entry in the database
    nova_vm_entry.status = "ACTIVE" # type: ignore
    nova_vm_entry.floating_ip = floating_ip.floating_ip_address # type: ignore
    nova_vm_entry.openstack_nova_vm_id = nova_vm.id # type: ignore
    db.session.commit()

    return nova_vm_entry

def wait_for_nova_vm_to_be_active(nova_vm_entry_id: int) -> NovaVM:
    nova_vm_entry: NovaVM = NovaVM.query.get(nova_vm_entry_id) # type: ignore
    while nova_vm_entry.status != "ACTIVE":
        print(f"Nova VM {nova_vm_entry.id} is not yet active. Waiting...") # type: ignore
        time.sleep(5)
        nova_vm_entry = NovaVM.query.get(nova_vm_entry_id) # type: ignore
    
    return nova_vm_entry

def delete_nova_instance(nova_instance_id: str):
    """Delete a Nova Instance, Floating IP, and associated port."""
    try:
        conn = get_openstack_connection()

        # Get Nova Instance from database
        nova_instance = NovaVM.query.filter_by(openstack_nova_vm_id=nova_instance_id).first() # type: ignore
        if not nova_instance:
            raise ValueError(f"Nova Instance with ID {nova_instance_id} not found in database.")

        # Delete from database
        db.session.delete(nova_instance) # type: ignore
        db.session.commit()
       
        ports = list(conn.network.ports(device_id=nova_instance.openstack_nova_vm_id)) # type: ignore

        for floating_ip in conn.network.ips(): # type: ignore
            if floating_ip.port_id: # type: ignore
                # Check if the floating IP is associated with the server's port
                port = conn.network.get_port(floating_ip.port_id) # type: ignore
                if port and port.device_id == nova_instance.openstack_nova_vm_id: # type: ignore
                    # Delete the floating IP
                    try:
                        conn.network.delete_ip(floating_ip) # type: ignore
                        print(f"Deleted Floating IP {floating_ip.floating_ip_address}") # type: ignore
                    except Exception as e:
                        print(f"Failed to delete Floating IP {floating_ip.floating_ip_address}: {str(e)}") # type: ignore
 
        # Delete instance on OpenStack
        conn.compute.delete_server(nova_instance.openstack_nova_vm_id, ignore_missing=True) # type: ignore
        try:
            conn.compute.wait_for_delete(nova_instance.openstack_nova_vm_id) # type: ignore
        except Exception as e:
            print(f"Failed to wait for delete: {str(e)}")

        # Delete associated ports
        for port in ports: # type: ignore
            try:
                conn.network.delete_port(port.id, ignore_missing=True) # type: ignore
            except Exception as e:
                print(f"Failed to delete port {port.id}: {str(e)}") # type: ignore

        return {"message": f"Nova Instance {nova_instance_id}, its Floating IP, and associated ports deleted successfully."}

    except Exception as e:
        raise RuntimeError(f"Failed to delete Nova Instance: {str(e)}")


# @choose_plan.route('/nova-instance', methods=['POST'])
# def api_select_or_create_nova_instance():
#     try:
#         data = request.get_json()
#         plan_id = data.get('plan_id')
#         if not plan_id:
#             return jsonify({"error": "plan_id is required"}), 400

#         nova_instance = select_or_create_nova_instance(plan_id)
#         return jsonify({
#             "nova_instance_id": nova_instance.id,
#             "floating_ip": nova_instance.floating_ip,
#             "status": nova_instance.status
#         }), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @choose_plan.route('/nova-instance/delete', methods=['DELETE'])
# def api_delete_nova_instance():
#     try:
#         data = request.get_json()
#         nova_instance_id = data.get('nova_instance_id')
#         if not nova_instance_id:
#             return jsonify({"error": "nova_instance_id is required"}), 400

#         result = delete_nova_instance(nova_instance_id)
#         return jsonify(result), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
