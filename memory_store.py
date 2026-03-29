
from models import Volunteer
from priority_engine import DisasterPriorityQueue

# ── Volunteer Storage
VOLUNTEER_MAP     = {}   # volunteer_id -> Volunteer object
VOLUNTEER_ORDERED = []   # ordered list for traversal
VOLUNTEER_GPS     = {}   # volunteer_id -> {lat, lon, timestamp}

# ── Disaster Storage
DISASTER_MAP   = {}                    # disaster_id -> Disaster object
DISASTER_QUEUE = DisasterPriorityQueue()  # heap-backed priority queue

# ── Blocked Roads (Union-Find simulation
BLOCKED_ROADS = []   # list of (location_a, location_b) tuples

# ── Demo Accounts
USERS = {"admin": "admin123"}
for _i in range(1, 21):         
    USERS[f"user{_i}"] = "1234"
for _i in range(101, 121):       
    USERS[f"v{_i}"] = "1234"


def seed_volunteers():
    """Create 20 volunteers across 8 skill groups, spread across city locations."""
    from graph_engine import DEHRADUN_LOCATIONS

    GROUPS = ["Medical", "NDRF", "Rescue", "Logistics",
              "Firefighting", "Search", "Transport", "Comms"]
    LOCATION_NAMES = list(DEHRADUN_LOCATIONS.keys())

    for i in range(101, 121):
        vid      = f"v{i}"
        group    = GROUPS[i % len(GROUPS)]
        location = LOCATION_NAMES[i % len(LOCATION_NAMES)]
        v        = Volunteer(vid, f"Personnel {i}", group)
        v.location = location
        VOLUNTEER_MAP[vid]  = v
        VOLUNTEER_ORDERED.append(v)


