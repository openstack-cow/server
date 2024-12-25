def q_check_health_of_all_websites() -> None:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import Website, NovaVM, db
        from app.utils.job_queue import get_job_queue
        from datetime import datetime
        try:
            try:
                websites: list[Website] = Website.query.filter_by(
                    # Filter websites with "ACTIVE" or "DOWN" status
                    status = "ACTIVE" # type: ignore
                ).all() # type: ignore

                websites.extend(Website.query.filter_by(
                    status = "DOWN" # type: ignore
                ).all()) # type: ignore

                websites.extend(Website.query.filter_by(
                    message = "Update successful" # type: ignore
                ).all()) # type: ignore

                for website in websites:
                    website_id = website.id
                    h = check_website_health(website_id, timeout_in_seconds = 300)
                    if h == "Healthy":
                        website.status = "ACTIVE"
                    elif h == "Unhealthy":
                        website.status = "DOWN"
                    website.message = f"Last checked: {datetime.now().isoformat()}"
            finally:
                db.session.commit()
            
            try:
                all_websites: list[Website] = Website.query.all() # type: ignore
                for website in all_websites:
                    if website.status == "CREATING": # type: ignore
                        # Inspect Nova VM ; if there is error then deem the website errored also
                        nova_vm_entry: NovaVM|None = NovaVM.query.get(website.nova_vm_id) # type: ignore
                        if not nova_vm_entry:
                            website.status = "ERROR"
                            website.message = "Nova VM not found"
                            continue
                        if nova_vm_entry.status == "ERROR":
                            website.status = "ERROR"
                            website.message = "Nova VM errored"
                            continue
            finally:
                db.session.commit()
                db.session.close()
        finally:
            get_job_queue().enqueue_in("1m", q_check_health_of_all_websites) # type: ignore

from typing import Literal
def check_website_health(website_id: int, timeout_in_seconds: int) -> Literal[
    "Healthy",
    "Unhealthy",
]:
    import time
    from app.models import Website, NovaVM
    from app.utils.ssh import create_ssh_client_to_nova_vm, execute_command

    website: Website = Website.query.get(website_id) # type: ignore
    if not website:
        raise ValueError(f"Website with ID {website_id} not found")
    
    nova_vm_entry: NovaVM = NovaVM.query.get(website.nova_vm_id) # type: ignore
    if not nova_vm_entry:
        raise ValueError(f"Nova VM with ID {website.nova_vm_id} not found")

    ssh_client = create_ssh_client_to_nova_vm(nova_vm_entry.floating_ip)

    start_time = time.time()

    try:
        while True:
            out, _err = execute_command(ssh_client, f"sudo docker inspect --format='{{{{.State.Health.Status}}}}' nodejs-app-{website.id}")
            if "healthy" in out:
                return "Healthy"
            if time.time() - start_time > timeout_in_seconds:
                return "Unhealthy"
            time.sleep(5)
    finally:
        ssh_client.close()
