
from models import Disaster, VolunteerUpdate
from memory_store import DISASTER_MAP, DISASTER_QUEUE, VOLUNTEER_MAP

def create_disaster_report(dtype, severity, is_emergency, volunteers_needed,
                            supplies_needed, description, reported_by, location, report_photo):
    """
    Create a new Disaster, store it in the map, and push it to the priority heap.

    Returns:
        int: ID of the newly created disaster
    """
    d = Disaster(
        dtype=dtype,
        severity=severity,
        is_emergency=is_emergency,
        volunteers_needed=volunteers_needed,
        supplies_needed=supplies_needed,
        description=description,
        reported_by=reported_by,
        location=location,
        report_photo=report_photo
    )
    DISASTER_MAP[d.id] = d
    DISASTER_QUEUE.push(d)
    return d.id


def get_all_disasters_sorted():
    """
    Returns all disasters sorted by heap priority (emergency > severity > time).
    Uses the priority queue's ordered view, not a plain dict traversal.
    """
    ordered = DISASTER_QUEUE.get_ordered_list()
    # Include disasters that might not be in queue (already resolved)
    resolved = [d for d in DISASTER_MAP.values() if d.status == "Resolved"]
    return [d.to_dict() for d in ordered] + [d.to_dict() for d in resolved]


def get_disasters_by_reporter(reporter_id):
    """Return all disasters filed by a specific user, sorted by priority."""
    results = [
        d for d in DISASTER_MAP.values()
        if d.reported_by == reporter_id
    ]
    results.sort(key=lambda d: (0 if d.is_emergency else 1, -d.severity, d.timestamp))
    return [d.to_dict() for d in results]


def get_disaster_by_id(disaster_id):
    return DISASTER_MAP.get(disaster_id)


def delete_disaster(disaster_id, reporter_id):
    """
    Delete a disaster only if:
      - It exists
      - The requester is the original reporter
      - Status is still Pending (admin hasn't acted on it)
    """
    d = DISASTER_MAP.get(disaster_id)
    if not d:
        return False, "Disaster not found."
    if d.reported_by != reporter_id:
        return False, "Permission denied. Only the original reporter can delete this."
    if d.status != "Pending":
        return False, f"Cannot delete. Status is '{d.status}' — admin is already handling it."

    DISASTER_QUEUE.remove(disaster_id)
    del DISASTER_MAP[disaster_id]
    return True, f"Disaster {disaster_id} deleted successfully."


def resolve_disaster(disaster_id, resolution_photo):
    """
    Mark a disaster as Resolved.
    Frees all assigned volunteers back to available status.
    """
    d = DISASTER_MAP.get(disaster_id)
    if not d or d.status == "Resolved":
        return False

    d.status = "Resolved"
    d.resolution_photo = resolution_photo
    DISASTER_QUEUE.remove(disaster_id)

    for vid in d.assigned_volunteers:
        v = VOLUNTEER_MAP.get(vid)
        if v:
            v.is_available = True
            v.assigned_to = None
            v.admin_message = None

    d.assigned_volunteers = []
    d.updates = []
    return True


def add_volunteer_update(disaster_id, volunteer_id, priority, description, update_photo=None):
    """Attach a field update from a volunteer to the disaster record."""
    d = DISASTER_MAP.get(disaster_id)
    if not d:
        return False
    update = VolunteerUpdate(disaster_id, volunteer_id, priority, description, update_photo)
    d.updates.append(update)
    return True
