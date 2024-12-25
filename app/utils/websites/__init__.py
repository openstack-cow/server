from typing import Literal
from ...models import Website, NovaVM, Plan, db
from app.utils.ssh import create_ssh_client_to_nova_vm, quick_shell_to_nova_vm, execute_command
from app.utils.openstack_api import get_openstack_connection
from datetime import datetime
from app.utils.job_queue import get_job_queue

WebsiteUpdateAction = Literal['start', 'stop', 'restart']

def create_new_website_in_docker(
    name: str, plan_id: int, user_id: int,
    user_code_zip_url: str, nova_vm_port: int,
) -> Website:
    # Get plan from db
    plan = Plan.query.get(plan_id)
    if not plan:
        raise ValueError(f"No plan found with id {plan_id}")
    
    from .choose_plan import select_or_create_nova_vm
    nova_vm_entry = select_or_create_nova_vm(plan_id)

    website = Website(
        name=name, # type: ignore
        user_id=user_id, # type: ignore
        plan_id=plan_id, # type: ignore
        status="CREATING", # type: ignore
        public_port=0, # type: ignore
        nova_vm_port=0, # type: ignore
        nova_vm_id=nova_vm_entry.id, # type: ignore
        created_at=int(datetime.now().timestamp()), # type: ignore
    )
    db.session.add(website)
    db.session.commit()

    from .q_create_new_website import q_create_new_website
    q = get_job_queue()
    q.enqueue(q_create_new_website, website.id) # type: ignore

    return website

def update_website_status(action: WebsiteUpdateAction, website_id: int):
    from app import db
    valid_actions = {"start", "stop", "restart"}
    if action not in valid_actions:
        raise ValueError(f"Invalid action '{action}'. Valid actions are: {valid_actions}")

    # Determine Nova VM
    nova_vm: NovaVM = Website.join(NovaVM, Website.nova_vm_id == NovaVM.id).filter( # type: ignore
        Website.id == website_id
    ).first() # type: ignore

    if nova_vm is None:
        raise ValueError(f"No website found with id {website_id}")

    nova_floating_ip: str = str(nova_vm.floating_ip) # type: ignore
    
    # Determine website
    website = Website.query.filter_by( # type: ignore
        id=website_id
    ).first()
    if not website:
        raise ValueError(f"No website found with id {website_id}")

    cmd = f"docker {action} nodejs-app-{website_id}"

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
