from ...models import Website, Plan, db
from datetime import datetime
from app.utils.job_queue import get_job_queue
from app.utils.websites.q_update_website_status import WebsiteUpdateAction

def create_new_website(
    name: str, plan_id: int, user_id: int,
    build_script: str, start_script: str,
    user_code_zip_url: str,
    port: int
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
        message="Queued", # type: ignore
        public_port=0, # type: ignore
        nova_vm_port=0, # type: ignore
        nova_vm_id=nova_vm_entry.id, # type: ignore
        port=port, # type: ignore
        build_script=build_script, # type: ignore
        start_script=start_script, # type: ignore
        code_zip_url=user_code_zip_url, # type: ignore
        created_at=int(datetime.now().timestamp()), # type: ignore
    )
    db.session.add(website)
    db.session.commit()

    from .q_create_new_website import q_create_new_website
    q = get_job_queue()
    q.enqueue(q_create_new_website, website.id) # type: ignore

    return website

def update_website_status(action: WebsiteUpdateAction, website_id: int) -> None:
    from app import db

    valid_actions = {"start", "stop", "restart"}
    if action not in valid_actions:
        raise ValueError(f"Invalid action '{action}'. Valid actions are: {valid_actions}")

    # Determine website
    website: Website|None = Website.query.filter_by( # type: ignore
        id=website_id
    ).first()
    if not website:
        raise ValueError(f"No website found with id {website_id}")

    if action == "start":
        website.status = "STARTING"
    elif action == "stop":
        website.status = "STOPPING"
    elif action == "restart":
        website.status = "RESTARTING"
    website.message = "Queued"
    db.session.commit()

    from .q_update_website_status import q_update_website_status
    q = get_job_queue()
    q.enqueue(q_update_website_status, action, website.id) # type: ignore

def delete_website(website_id: int) -> None:
    from app import db

    website = Website.query.get(website_id)
    if not website:
        raise ValueError(f"No website found with id {website_id}")

    website.status = "DELETING"
    website.message = "Queued"
    db.session.commit()

    from .q_delete_website import q_delete_website
    q = get_job_queue()
    q.enqueue(q_delete_website, website.id) # type: ignore
