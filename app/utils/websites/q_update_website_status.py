from typing import Literal

WebsiteUpdateAction = Literal['start', 'stop', 'restart']

def q_update_website_status(action: WebsiteUpdateAction, website_id: int):
    from app import create_app
    app = create_app()

    with app.app_context():
        from app.models import Website, NovaVM, db
        from app.utils.ssh import quick_shell_to_nova_vm
        # Determine website
        website: Website|None = Website.query.filter_by( # type: ignore
            id=website_id
        ).first()
        if not website:
            raise ValueError(f"No website found with id {website_id}")

        # Determine Nova VM
        nova_vm: NovaVM|None = NovaVM.query.get(website.nova_vm_id) # type: ignore
        if not nova_vm:
            raise ValueError(f"No website found with id {website_id}")

        try:
            nova_floating_ip: str = str(nova_vm.floating_ip) # type: ignore
            cmd = f"docker {action} nodejs-app-{website_id}"
            quick_shell_to_nova_vm(nova_floating_ip, cmd)

            website.message = "Update successful"
            db.session.commit()
        except Exception as e:
            website.status = "DOWN"
            website.message = f"Update failed: {str(e)}"
            db.session.commit()
            raise e
