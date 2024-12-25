def q_delete_website(website_id: int) -> None:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import Website, NovaVM, db

        website: Website|None = Website.query.get(website_id)
        if not website:
            raise ValueError(f"No website found with id {website_id}")
        
        nova_vm: NovaVM|None = NovaVM.query.get(website.nova_vm_id)
        if not nova_vm:
            raise ValueError(f"No Nova VM found with id {website.nova_vm_id}")
        
        from app.utils.websites.port_assignment import unassign_public_port
        from app.utils.ssh import create_ssh_client_to_nova_vm, execute_command

        ssh_client = create_ssh_client_to_nova_vm(nova_vm.floating_ip)
        try:
            website.status = "DELETING"
            website.message = "Unassigning public port"
            db.session.commit()
            unassign_public_port(website.public_port, nova_vm.floating_ip, website.nova_vm_port)

            website.status = "DELETING"
            website.message = "Deleting Docker containers and volumes"
            db.session.commit()
            execute_command(ssh_client, f"cd ~/{website_id}")
            execute_command(ssh_client, f"docker-compose down -v")

            website.status = "DELETING"
            website.message = "Deleting source code"
            db.session.commit()
            execute_command(ssh_client, f"rm -rf ~/{website_id}")

            db.session.delete(website)
        except Exception as e:
            website.status = "DELETING"
            website.message = f"Delete failed: {str(e)}"
            db.session.commit()
            raise e
        finally:
            ssh_client.close()
