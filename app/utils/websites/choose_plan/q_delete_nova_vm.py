def q_delete_nova_vm(nova_vm_entry_id: int) -> None:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.utils.openstack_api import get_openstack_connection
        from app.models import NovaVM, db

        nova_vm_entry = NovaVM.query.get(nova_vm_entry_id)
        if not nova_vm_entry:
            raise ValueError(f"Nova VM with ID {nova_vm_entry_id} not found")
        
        conn = get_openstack_connection()

        ports = list(conn.network.ports(device_id=nova_vm_entry.openstack_nova_vm_id)) # type: ignore

        for floating_ip in conn.network.ips(): # type: ignore
            if floating_ip.port_id: # type: ignore
                # Check if the floating IP is associated with the server's port
                port = conn.network.get_port(floating_ip.port_id) # type: ignore
                if port and port.device_id == nova_vm_entry.openstack_nova_vm_id: # type: ignore
                    # Delete the floating IP
                    try:
                        conn.network.delete_ip(floating_ip) # type: ignore
                        print(f"Deleted Floating IP {floating_ip.floating_ip_address}") # type: ignore
                    except Exception as e:
                        print(f"Failed to delete Floating IP {floating_ip.floating_ip_address}: {str(e)}") # type: ignore

        # Delete VM in OpenStack
        conn.compute.delete_server(nova_vm_entry.openstack_nova_vm_id, ignore_missing=True) # type: ignore
        try:
            conn.compute.wait_for_delete(nova_vm_entry.openstack_nova_vm_id) # type: ignore
        except Exception as e:
            print(f"Failed to wait for delete: {str(e)}")

        # Delete associated ports
        for port in ports: # type: ignore
            try:
                conn.network.delete_port(port.id, ignore_missing=True) # type: ignore
            except Exception as e:
                print(f"Failed to delete port {port.id}: {str(e)}") # type: ignore

        # Delete from database
        db.session.delete(nova_vm_entry)
