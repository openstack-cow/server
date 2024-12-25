def q_create_new_website(website_id: int) -> None:
    import logging
    logging.basicConfig(filename="q_create_new_website.log", level=logging.DEBUG)
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import Website, NovaVM, Plan, db
        from app.utils.websites.choose_plan import wait_for_nova_vm_to_be
        website: Website|None = Website.query.get(website_id)
        if not website:
            raise ValueError(f"Website with ID {website_id} not found")
        
        try:
            logging.debug(f"Waiting for Nova VM with entry ID {website.nova_vm_id} to be ready")
            website.status = "CREATING"
            website.message = "Waiting for Nova virtual machine to be ready"
            db.session.commit()

            wait_for_nova_vm_to_be(website.nova_vm_id, "ACTIVE")
            logging.debug(f"VM ready.")
            
            nova_vm_entry: NovaVM = NovaVM.query.get(website.nova_vm_id) # type: ignore
            if not nova_vm_entry:
                raise ValueError(f"Nova VM with ID {website.nova_vm_id} not found")
            
            plan = Plan.query.get(website.plan_id)
            if not plan:
                raise ValueError(f"Plan with ID {website.plan_id} not found")
            
            logging.debug("Reporting status")
            website.status = "CREATING"
            website.message = "Creating Docker containers"
            db.session.commit()

            nova_floating_ip = nova_vm_entry.floating_ip
            openstack_nova_vm_id = nova_vm_entry.openstack_nova_vm_id

            logging.debug("Connecting to OpenStack Nova")
            from app.utils.openstack_api import get_openstack_connection
            openstack = get_openstack_connection()
            openstack_nova_vm = openstack.compute.get_server(openstack_nova_vm_id) # type: ignore
            openstack.compute.wait_for_server(openstack_nova_vm) # type: ignore
            
            logging.debug(f"SSH into Nova VM at {nova_floating_ip}")
            from app.utils.ssh import create_ssh_client_to_nova_vm, execute_command
            ssh_client = create_ssh_client_to_nova_vm(nova_floating_ip)
            try:
                logging.debug("SSH successful")
                logging.debug("Downloading source code")
                execute_command(ssh_client, f"mkdir -p ~/{website.id}")
                execute_command(ssh_client, f"wget -O source-{website.id}.zip {website.code_zip_url}")

                logging.debug("Extracting source code")
                # Check if the downloaded file is a zip file
                out, _err = execute_command(ssh_client, f"file source-{website.id}.zip")
                try:
                    if "Zip archive data" not in out:
                        raise ValueError("Downloaded file is not a zip archive")
                    execute_command(ssh_client, f"unzip source-{website.id}.zip -d ~/{website.id}")
                finally:
                    execute_command(ssh_client, f"rm source-{website.id}.zip")
                
                logging.debug("Creating Docker files")
                from app.utils.websites.choose_plan.write_dockerfiles import write_docker_files
                write_docker_files(
                    ssh_client,
                    plan_name=plan.name,
                    dir_path=f"~/{website.id}/",
                    website_id=website.id,
                    app_port=website.port,
                    build_script=website.build_script,
                    start_script=website.start_script,
                )

                logging.debug("Building and running Docker images")
                execute_command(ssh_client, f"bash -c \"cd ~/{website.id} && sudo docker compose -p website_{website.id} up --build -d\"")

                logging.debug("Waiting for Node.js container to be ready")
                website.status = "CREATING"
                website.message = "Waiting for Node.js container to be ready"
                db.session.commit()

                # Health check
                from app.utils.websites.q_check_website_health import check_website_health
                h = check_website_health(website.id, timeout_in_seconds = 300)
                if h == "Unhealthy":
                    raise TimeoutError("Node.js website failed to start in time")

                logging.debug("Exposing port from Docker")
                website.status = "CREATING"
                website.message = "Assigning public address"
                db.session.commit()

                # Retrieve the dynamically-assigned internal port
                out, _err = execute_command(ssh_client, f"sudo docker compose -p website_{website.id} port app {website.port}")
                nova_vm_port = int(out.split(":")[1].strip())
                website.nova_vm_port = nova_vm_port
                db.session.commit()

                logging.debug("Assigning public port for external access")
                # Get the public port
                from app.utils.websites.port_assignment import assign_public_port
                public_port = assign_public_port(nova_vm_entry.floating_ip, nova_vm_port)
                website.public_port = public_port
                website.status = "ACTIVE"
                website.message = ""
                db.session.commit()
            finally:
                ssh_client.close()
                logging.debug("Finished")
        except Exception as e:
            website.status = "ERROR"
            website.message = str(e)
            db.session.commit()
            logging.debug(f"Error: {e}")
            raise e
