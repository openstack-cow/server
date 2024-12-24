from flask import Blueprint, request, jsonify, render_template
import json
from .utils.openstack_api import get_openstack_connection


openstack_service = Blueprint('openstack_service', __name__)


@openstack_service.route("/create_floating_ips", methods=["POST"])
def create_floating_ip():
    conn = get_openstack_connection()
    # Find or create a floating IP
    floating_ip = conn.network.find_available_ip()

    print(floating_ip)
    if not floating_ip:
        floating_ip = conn.network.create_ip(floating_network_id=network.id)

    return jsonify({"floating_ip": floating_ip.floating_ip_address}), 200

@openstack_service.route("/create_instance", methods=["POST"])
def create_instance():
    conn = get_openstack_connection()
    # List all instances (Nova)
    print("Instances:")
    for server in conn.compute.servers():
        print(server)

    # List all images (Glance)
    print("Images:")
    for image in conn.image.images():
        print(image.name)

    # List all networks (Neutron)
    print("Networks:")
    for network in conn.network.networks():
        print(network.name)

    # # Create a volume (Cinder)
    # volume = conn.block_store.create_volume(
    #     size=10,  # Size in GB
    #     name="test-volume",
    #     description="My test volume"
    # )
    # print(f"Volume {volume.name} is being created.")

    # possible flavors: m1.tiny, m1.small, m1.medium, m1.large
    # Create a new server instance
    # flavor = conn.compute.find_flavor("m1.tiny")
    # image = conn.compute.find_image("ubuntu")
    # network = conn.network.find_network("external-network")

    # try:
    #     server = conn.compute.create_server(
    #         name="test-server",
    #         flavor_id=flavor.id,
    #         image_id=image.id,
    #         networks=[{"uuid": network.id}],
    #     )
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400
    return jsonify({"status": "success"}), 200


@openstack_service.route("/ssh_instance", methods=["POST"])
def ssh_instance():
    conn = get_openstack_connection()




    return jsonify({"status": "success"}), 200
