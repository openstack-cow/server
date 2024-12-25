def q_create_new_nova_vm(nova_vm_entry_id: int) -> None:
    from app import create_app
    from app.models import NovaVM
    from app.utils.openstack_api import get_openstack_connection
    from app.env import NOVA_VM_FLAVOR_ID, NOVA_VM_IMAGE_ID, NOVA_VM_NETWORK_ID, NOVA_VM_SECURITY_GROUP_NAME, NOVA_VM_KEYPAIR_NAME, NOVA_VM_EXTERNAL_NETWORK_ID
    from app.models import db
    import time

    import logging
    logging.basicConfig(filename='q_create_new_nova.log', level=logging.DEBUG)

    app = create_app()
    with app.app_context():
        nova_vm_entry: NovaVM|None = NovaVM.query.get(nova_vm_entry_id) # type: ignore
        if not nova_vm_entry:
            raise ValueError(f"Nova VM with ID {nova_vm_entry_id} not found")

        try:
            conn = get_openstack_connection()

            logging.debug(f"Creating Nova VM with ID {nova_vm_entry.id}")
            nova_vm = conn.compute.create_server( # type: ignore
                name="vm_" + str(nova_vm_entry.id),
                flavorRef=NOVA_VM_FLAVOR_ID,
                imageRef=NOVA_VM_IMAGE_ID,
                networks=[{"uuid": NOVA_VM_NETWORK_ID}],
                security_groups=[{ "name": NOVA_VM_SECURITY_GROUP_NAME }],
                key_name=NOVA_VM_KEYPAIR_NAME
            )
            nova_vm = conn.compute.wait_for_server(nova_vm) # type: ignore

            logging.debug(f"Nova VM created with ID {nova_vm.id}") # type: ignore
            nova_vm_entry.openstack_nova_vm_id = nova_vm.id # type: ignore
            db.session.commit()

            logging.debug(f"Nova VM status: {nova_vm.status}") # type: ignore
            logging.debug(f"Getting Nova VM ports...") # type: ignore
            # Get the port ID associated with the VM
            ports = list(conn.network.ports(device_id=nova_vm.id))  # type: ignore
            if not ports:
                raise RuntimeError(f"No ports found for Nova VM {nova_vm.id}") # type: ignore
            port_id = ports[0].id  # Assuming the first port is the one we want # type: ignore
            logging.debug(f"Found Nova VM port ID: {port_id}") # type: ignore

            logging.debug(f"Create and attach Floating IP to the specific port")
            floating_ip = conn.network.create_ip(floating_network_id=NOVA_VM_EXTERNAL_NETWORK_ID) # type: ignore
            conn.network.update_ip(floating_ip, port_id=port_id) # type: ignore
            logging.debug(f"Floating IP created: {floating_ip.floating_ip_address}") # type: ignore
            nova_vm_entry.floating_ip = str(floating_ip.floating_ip_address) # type: ignore
            db.session.commit()

            logging.debug(f"Run SSH command to check if the connection is successful")
            from app.utils.ssh import create_ssh_client_to_nova_vm, execute_command
            ssh_client = None
            while True:
                try:
                    ssh_client = create_ssh_client_to_nova_vm(nova_vm_entry.floating_ip)
                    break
                except Exception as e:
                    logging.debug(f"SSH connection failed with exception: {e}. Retrying after 5 seconds...")
                    time.sleep(5)
                    continue
            
            logging.debug(f"Setup new Nova VM with necessary commands")
            try:
                logging.debug(f"Setting up DNS first and foremost!")
                execute_command(ssh_client, "sudo resolvectl dns $(ip route | awk '/default/ {print $5; exit}') 8.8.8.8")
                execute_command(ssh_client, "ping -c 4 supabase.co")

                logging.debug(f"Update and install necessary packages")
                execute_command(ssh_client, "sudo apt update")
                execute_command(ssh_client, "sudo apt install -y bash wget unzip")

                logging.debug(f"Download and run the setup script")
                execute_command(ssh_client, "wget -O setup_nova_vm.sh https://iweptimpblcxlwztoziq.supabase.co/storage/v1/object/public/iaas/scripts/setup_nova_vm.sh")
                execute_command(ssh_client, "chmod +x setup_nova_vm.sh")
                execute_command(ssh_client, "bash setup_nova_vm.sh")
            finally:
                ssh_client.close()

            logging.debug(f"Update the NovaVM entry in the database")
            nova_vm_entry.status = "ACTIVE" # type: ignore
            db.session.commit()
        except Exception as e:
            logging.error(f"Failed to create Nova VM: {str(e)}")
            nova_vm_entry.status = "ERROR" # type: ignore
            db.session.commit()
            # raise e
