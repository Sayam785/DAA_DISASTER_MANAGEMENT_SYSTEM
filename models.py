# core/models.py
# Data model definitions for Disaster, Volunteer, and related entities

from datetime import datetime


class Volunteer:
    """Represents an emergency response volunteer."""

    def __init__(self, vid, name, group):
        self.id = vid
        self.name = name
        self.group = group
        self.is_available = True
        self.assigned_to = None          # disaster ID if assigned
        self.admin_message = None        # deployment instructions from admin
        self.location = None             # current city location (node name)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "group": self.group,
            "is_available": self.is_available,
            "assigned_to": self.assigned_to,
            "admin_message": self.admin_message,
            "location": self.location,
        }


class VolunteerUpdate:
    """A field update sent by a volunteer back to admin during an active mission."""

    def __init__(self, disaster_id, volunteer_id, priority, description, update_photo=None):
        self.disaster_id = disaster_id
        self.volunteer_id = volunteer_id
        self.priority = priority          # "Normal" | "Crisis" | "Casualty"
        self.description = description
        self.update_photo = update_photo
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {
            "disaster_id": self.disaster_id,
            "volunteer_id": self.volunteer_id,
            "priority": self.priority,
            "description": self.description,
            "update_photo": self.update_photo,
            "timestamp": self.timestamp,
        }


class Disaster:
    """Represents a disaster report submitted by a user."""

    _id_counter = 1

    def __init__(self, dtype, severity, is_emergency, volunteers_needed,
                 supplies_needed, description, reported_by, location, report_photo):
        self.id = Disaster._id_counter
        Disaster._id_counter += 1

        self.type = dtype
        self.severity = int(severity)
        self.is_emergency = bool(is_emergency)
        self.volunteers_needed = int(volunteers_needed)
        self.supplies_needed = supplies_needed    # comma-separated string
        self.description = description
        self.reported_by = reported_by
        self.location = location                 # must match a city graph node
        self.report_photo = report_photo

        self.status = "Pending"                  # Pending | InProgress | Resolved
        self.timestamp = datetime.now()
        self.assigned_volunteers = []            # list of volunteer IDs
        self.updates = []                        # list of VolunteerUpdate objects
        self.resolution_photo = None
        self.resolution_feedback = None

    @property
    def assigned_count(self):
        return len(self.assigned_volunteers)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "is_emergency": self.is_emergency,
            "priority_type": "Emergency" if self.is_emergency else "Normal",
            "volunteers_needed": self.volunteers_needed,
            "assignedCount": self.assigned_count,
            "assigned_volunteers": self.assigned_volunteers,
            "supplies_needed": self.supplies_needed,
            "description": self.description,
            "reported_by": self.reported_by,
            "location": self.location,
            "status": self.status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "report_photo": self.report_photo,
            "resolution_photo": self.resolution_photo,
            "resolution_feedback": self.resolution_feedback,
            "updates": [u.to_dict() for u in self.updates],
        }
