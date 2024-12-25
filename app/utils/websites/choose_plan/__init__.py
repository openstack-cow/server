import time
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, NovaVM, Plan
from app.utils.openstack_api import get_openstack_connection
from app.env import NOVA_VM_FLAVOR_ID

from typing import TypedDict

class NovaVMResourceStats(TypedDict):
    cpu_cores: int
    ram_in_mb: int
    storage_in_mb: int

class NovaVMSelectionResult(TypedDict):
    nova_vm_entry: NovaVM
    remaining_resources: NovaVMResourceStats

def select_or_create_nova_vm(plan_id: int) -> NovaVM:
    plan = Plan.query.filter_by(id=plan_id).first() # type: ignore
    if not plan:
        raise ValueError("Plan not found.")

    nova_vms = NovaVM.query.filter(NovaVM.status.in_(["ACTIVE", "CREATING"])).all() # type: ignore

    for nova_vm in nova_vms: # type: ignore
        stats = calculate_nova_vm_stats(nova_vm.id) # type: ignore
        if stats and all(
            stats["remaining_resources"][key] >= getattr(plan, key) # type: ignore
            for key in ["cpu_cores", "ram_in_mb", "storage_in_mb"]
        ):
            return nova_vm # type: ignore

    return create_new_nova_vm()

def create_new_nova_vm() -> NovaVM:
    nova_vm_entry = NovaVM(
        status="CREATING", # type: ignore
        floating_ip="(Unknown)", # type: ignore
        openstack_nova_vm_id="(Unknown)" # type: ignore
    )
    db.session.add(nova_vm_entry)
    db.session.commit()

    from app.utils.job_queue import get_job_queue
    from app.utils.websites.choose_plan.q_create_new_nova_vm import q_create_new_nova_vm
    q = get_job_queue()
    q.enqueue(q_create_new_nova_vm, nova_vm_entry.id) # type: ignore

    return nova_vm_entry

from typing import Literal

def wait_for_nova_vm_to_be(nova_vm_entry_id: int, status: Literal['ACTIVE', 'DELETED']) -> NovaVM:
    nova_vm_entry: NovaVM = NovaVM.query.get(nova_vm_entry_id) # type: ignore
    while nova_vm_entry.status != status:
        print(f"Nova VM {nova_vm_entry.id} is not yet active. Waiting...") # type: ignore
        time.sleep(5)
        nova_vm_entry = NovaVM.query.get(nova_vm_entry_id) # type: ignore
    return nova_vm_entry

def delete_nova_vm(nova_vm_entry_id: str):
    """Delete a Nova VM, Floating IP, and associated port."""
    nova_vm_entry = NovaVM.query.get(nova_vm_entry_id) # type: ignore
    if not nova_vm_entry:
        raise ValueError(f"Nova VM with ID {nova_vm_entry_id} not found.")

    nova_vm_entry.status = "DELETING" # type: ignore
    db.session.commit()

    from app.utils.job_queue import get_job_queue
    from app.utils.websites.choose_plan.q_delete_nova_vm import q_delete_nova_vm
    q = get_job_queue()
    q.enqueue(q_delete_nova_vm, nova_vm_entry.id) # type: ignore

    return nova_vm_entry



####################################





def get_total_resources_from_flavor() -> dict[str, int]:
    """Get total resources of the Nova VM using the flavor ID from OpenStack."""
    try:
        conn = get_openstack_connection()
        flavor = conn.compute.get_flavor(NOVA_VM_FLAVOR_ID) # type: ignore
        if not flavor:
            raise ValueError(f"Flavor with ID {NOVA_VM_FLAVOR_ID} not found.")

        return {
            "cpu_cores": 2 * flavor.vcpus, # type: ignore
            "ram_in_mb": flavor.ram, # type: ignore
            "storage_in_mb": flavor.disk*1024  # Convert GB to MB # type: ignore
        }

    except Exception as e:
        raise RuntimeError(f"Failed to fetch flavor details: {str(e)}")

from typing import Optional

def calculate_nova_vm_stats(nova_vm_id: int) -> NovaVMSelectionResult:
    """Thống kê tài nguyên đã sử dụng và còn lại trong một Nova VM."""
    try:
        nova_vm: Optional[NovaVM] = NovaVM.query.filter_by(id=nova_vm_id).first() # type: ignore
        if not nova_vm:
            raise ValueError(f"Nova VM with ID {nova_vm_id} not found.")

        total_resources = get_total_resources_from_flavor()

        print(total_resources)

        websites = nova_vm.websites  # Assume a relationship is defined # type: ignore
        used_resources = {
            "cpu_cores": sum(website.plan.cpu_cores for website in websites), # type: ignore
            "ram_in_mb": sum(website.plan.ram_in_mb for website in websites), # type: ignore
            "storage_in_mb": sum(website.plan.storage_in_mb for website in websites) # type: ignore
        }

        print(used_resources)

        remaining_resources: NovaVMResourceStats = {
            "cpu_cores": total_resources["cpu_cores"] - used_resources["cpu_cores"],
            "ram_in_mb": total_resources["ram_in_mb"] - used_resources["ram_in_mb"],
            "storage_in_mb": total_resources["storage_in_mb"] - used_resources["storage_in_mb"]
        }
        print(remaining_resources)

        return {
            "nova_vm_entry": nova_vm,
            "remaining_resources": remaining_resources
        }

    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")
