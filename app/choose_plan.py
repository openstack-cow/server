
import time
import random
from flask import Blueprint, jsonify, request
import os
from sqlalchemy.exc import SQLAlchemyError
from .models import db, NovaVM, Plan
from .utils.openstack_api import get_openstack_connection
from .env import (NOVA_VM_FLAVOR_ID, NOVA_VM_IMAGE_ID, NOVA_VM_NETWORK_ID, 
                 NOVA_VM_SECURITY_GROUP_ID, NOVA_VM_KEYPAIR_NAME, 
                 NOVA_VM_PRIVATE_KEY_PATH, NOVA_VM_EXTERNAL_NETWORK_ID)

choose_plan = Blueprint('choosePlan', __name__)

def get_total_resources_from_flavor():
    """Get total resources of the Nova Instance using the flavor ID from OpenStack."""
    try:
        conn = get_openstack_connection()
        flavor = conn.compute.get_flavor(NOVA_VM_FLAVOR_ID)
        if not flavor:
            raise ValueError(f"Flavor with ID {NOVA_VM_FLAVOR_ID} not found.")

        return {
            "cpu_cores": 2*flavor.vcpus,
            "ram_in_mb": flavor.ram,
            "storage_in_mb": flavor.disk*1024  # Convert GB to MB
        }

    except Exception as e:
        raise RuntimeError(f"Failed to fetch flavor details: {str(e)}")

def calculate_nova_instance_stats(nova_vm_id):
    """Thống kê tài nguyên đã sử dụng và còn lại trong một Nova Instance."""
    try:
        nova_instance = NovaVM.query.filter_by(id=nova_vm_id).first()
        if not nova_instance:
            return None

        total_resources = get_total_resources_from_flavor()

        print(total_resources)

        websites = nova_instance.websites  # Assume a relationship is defined
        used_resources = {
            "cpu_cores": sum(website.plan.cpu_cores for website in websites),
            "ram_in_mb": sum(website.plan.ram_in_mb for website in websites),
            "storage_in_mb": sum(website.plan.storage_in_mb for website in websites)
        }

        print(used_resources)

        remaining_resources = {
            "cpu_cores": total_resources["cpu_cores"] - used_resources["cpu_cores"],
            "ram_in_mb": total_resources["ram_in_mb"] - used_resources["ram_in_mb"],
            "storage_in_mb": total_resources["storage_in_mb"] - used_resources["storage_in_mb"]
        }
        print(remaining_resources)

        return {
            "nova_instance": nova_instance,
            "remaining_resources": remaining_resources
        }

    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")
    
def select_or_create_nova_instance(plan_id):
    plan = Plan.query.filter_by(id=plan_id).first()
    if not plan:
        raise ValueError("Plan not found.")

    nova_instances = NovaVM.query.filter_by(status="ACTIVE").all()

    for nova_instance in nova_instances:
        stats = calculate_nova_instance_stats(nova_instance.id)
        if stats and all(
            stats["remaining_resources"][key] >= getattr(plan, key)
            for key in ["cpu_cores", "ram_in_mb", "storage_in_mb"]
        ):
            return nova_instance

    return create_new_nova_instance()

def create_new_nova_instance():
    conn = get_openstack_connection()

    instance = conn.compute.create_server(
        name="new-nova-instance"+str(random.randint(1,100))+str(time.time()),
        flavorRef=NOVA_VM_FLAVOR_ID,
        imageRef=NOVA_VM_IMAGE_ID,
        networks=[{"uuid": NOVA_VM_NETWORK_ID}],
        security_groups=[{ "name": "default" }],
        key_name=NOVA_VM_KEYPAIR_NAME
    )
    instance = conn.compute.wait_for_server(instance)

    # Get the port ID associated with the instance
    ports = list(conn.network.ports(device_id=instance.id)) 
    if not ports:
        raise RuntimeError(f"No ports found for instance {instance.id}")
    port_id = ports[0].id  # Assuming the first port is the one we want

    # Create and attach Floating IP to the specific port
    floating_ip = conn.network.create_ip(floating_network_id=NOVA_VM_EXTERNAL_NETWORK_ID)
    conn.network.update_ip(floating_ip, port_id=port_id)

    nova_instance = NovaVM(
        status="ACTIVE",
        floating_ip=floating_ip.floating_ip_address,
        openstack_nova_vm_id=instance.id
    )
    db.session.add(nova_instance)
    db.session.commit()

    return nova_instance

def delete_nova_instance(nova_instance_id):
    """Delete a Nova Instance, Floating IP, and associated port."""
    try:
        conn = get_openstack_connection()

        # Get Nova Instance from database
        nova_instance = NovaVM.query.filter_by(openstack_nova_vm_id=nova_instance_id).first()
        if not nova_instance:
            raise ValueError(f"Nova Instance with ID {nova_instance_id} not found in database.")

        # Delete from database
        db.session.delete(nova_instance)
        db.session.commit()
       
        ports = list(conn.network.ports(device_id=nova_instance.openstack_nova_vm_id))

        for floating_ip in conn.network.ips():
            if floating_ip.port_id:
                # Check if the floating IP is associated with the server's port
                port = conn.network.get_port(floating_ip.port_id)
                if port and port.device_id == nova_instance.openstack_nova_vm_id:
                    # Delete the floating IP
                    try:
                        conn.network.delete_ip(floating_ip)
                        print(f"Deleted Floating IP {floating_ip.floating_ip_address}")
                    except Exception as e:
                        print(f"Failed to delete Floating IP {floating_ip.floating_ip_address}: {str(e)}")
 

        # Delete instance on OpenStack
        conn.compute.delete_server(nova_instance.openstack_nova_vm_id, ignore_missing=True)
        try:
            conn.compute.wait_for_delete(nova_instance.openstack_nova_vm_id)
        except Exception as e:
            print(f"Failed to wait for delete: {str(e)}")

        # Delete associated ports
        for port in ports:
            try:
                conn.network.delete_port(port.id, ignore_missing=True)
            except Exception as e:
                print(f"Failed to delete port {port.id}: {str(e)}")


        return {"message": f"Nova Instance {nova_instance_id}, its Floating IP, and associated ports deleted successfully."}

    except Exception as e:
        raise RuntimeError(f"Failed to delete Nova Instance: {str(e)}")


@choose_plan.route('/nova-instance', methods=['POST'])
def api_select_or_create_nova_instance():
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        if not plan_id:
            return jsonify({"error": "plan_id is required"}), 400

        nova_instance = select_or_create_nova_instance(plan_id)
        return jsonify({
            "nova_instance_id": nova_instance.id,
            "floating_ip": nova_instance.floating_ip,
            "status": nova_instance.status
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@choose_plan.route('/nova-instance/delete', methods=['DELETE'])
def api_delete_nova_instance():
    try:
        data = request.get_json()
        nova_instance_id = data.get('nova_instance_id')
        if not nova_instance_id:
            return jsonify({"error": "nova_instance_id is required"}), 400

        result = delete_nova_instance(nova_instance_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
