# services/volunteer_service.py
# Handles volunteer assignment, retrieval, and status management.

from memory_store import VOLUNTEER_MAP, VOLUNTEER_ORDERED, VOLUNTEER_GPS, DISASTER_MAP


def get_all_volunteers():
    """Return all volunteers with their GPS data merged in."""
    result = []
    for v in VOLUNTEER_ORDERED:
        data = v.to_dict()
        data["location_data"] = VOLUNTEER_GPS.get(v.id, {
            "lat": "N/A", "lon": "N/A", "timestamp": "Never"
        })
        result.append(data)
    return result


def get_volunteer(volunteer_id):
    return VOLUNTEER_MAP.get(volunteer_id)


def assign_volunteer_to_disaster(disaster_id, volunteer_id, deployment_message):
    """
    Assign a volunteer to a disaster if:
      - Both exist
      - Volunteer is available
      - Disaster still needs more volunteers
    """
    d = DISASTER_MAP.get(disaster_id)
    v = VOLUNTEER_MAP.get(volunteer_id)

    if not d or not v:
        return False, "Disaster or volunteer not found."
    if not v.is_available:
        return False, f"Volunteer {volunteer_id} is already deployed."
    if d.assigned_count >= d.volunteers_needed:
        return False, f"Disaster {disaster_id} already has enough volunteers assigned."
    if d.status == "Resolved":
        return False, "Cannot assign to a resolved disaster."

    d.assigned_volunteers.append(volunteer_id)
    d.status = "InProgress"
    v.is_available = False
    v.assigned_to = disaster_id
    v.admin_message = deployment_message
    return True, f"Volunteer {volunteer_id} assigned to disaster {disaster_id}."


def auto_assign_volunteers(disaster_id, deployment_message):
    """
    Automatically fill remaining volunteer slots for a disaster
    by iterating through available volunteers in order.
    """
    d = DISASTER_MAP.get(disaster_id)
    if not d:
        return False, "Disaster not found."
    if d.status == "Resolved":
        return False, "Disaster already resolved."

    assigned_count_before = d.assigned_count
    slots_remaining = d.volunteers_needed - d.assigned_count

    for v in VOLUNTEER_ORDERED:
        if slots_remaining <= 0:
            break
        if v.is_available:
            success, _ = assign_volunteer_to_disaster(disaster_id, v.id, deployment_message)
            if success:
                slots_remaining -= 1

    newly_assigned = d.assigned_count - assigned_count_before
    if newly_assigned == 0:
        return False, "No available volunteers found for auto-assignment."

    return True, f"{newly_assigned} volunteer(s) auto-assigned to disaster {disaster_id}."


def update_volunteer_gps(volunteer_id, lat, lon, timestamp):
    """Store GPS coordinates from a volunteer's browser."""
    VOLUNTEER_GPS[volunteer_id] = {"lat": lat, "lon": lon, "timestamp": timestamp}
    return True


def get_volunteer_assignment_details(volunteer_id):
    """
    Return all assignment info a volunteer needs for their Mission Hub:
    - disaster details
    - admin message
    - team mates
    """
    v = VOLUNTEER_MAP.get(volunteer_id)
    if not v:
        return None

    result = v.to_dict()

    if v.assigned_to:
        d = DISASTER_MAP.get(v.assigned_to)
        if d:
            result["disaster_details"] = d.to_dict()
            result["team_members"] = [
                vid for vid in d.assigned_volunteers if vid != volunteer_id
            ]
        else:
            result["disaster_details"] = None
            result["team_members"] = []
    else:
        result["disaster_details"] = None
        result["team_members"] = []

    return result
