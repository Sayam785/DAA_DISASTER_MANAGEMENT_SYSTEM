
from optimisation_engine import knapsack_optimize, get_supplies_allocation
from unionfind_engine import build_connectivity_map, check_pair_connectivity
from graph_engine import CITY_GRAPH
from memory_store import VOLUNTEER_MAP, DISASTER_MAP, BLOCKED_ROADS


def run_knapsack_for_disaster(disaster_id):
    """
    Run the 0/1 Knapsack DP to find the optimal volunteer subset
    for a given disaster, constrained by resource budget.

    Returns:
        dict with selected volunteers, total skill value, cost used, and budget
    """
    d = DISASTER_MAP.get(disaster_id)
    if not d:
        return {"error": f"Disaster {disaster_id} not found."}

   
    available_volunteers = [
        v.to_dict() for v in VOLUNTEER_MAP.values() if v.is_available
    ]

    if not available_volunteers:
        return {
            "error": "No available volunteers to optimize.",
            "disaster_id": disaster_id
        }

    result = knapsack_optimize(
        volunteers=available_volunteers,
        disaster_type=d.type
    )

   
    supplies_result = None
    if d.supplies_needed:
        supply_items = [s.strip() for s in d.supplies_needed.split(",") if s.strip()]
        if supply_items:
            supplies_result = get_supplies_allocation(supply_items)

    return {
        "disaster_id": disaster_id,
        "disaster_type": d.type,
        "disaster_location": d.location,
        "knapsack_result": result,
        "supplies_optimization": supplies_result,
    }


def run_connectivity_check(blocked_edges=None):
    """
    Run Union-Find on the city graph (with optional blocked edges)
    to check if all locations are still reachable from each other.

    Args:
        blocked_edges: list of {from, to} dicts (from frontend)

    Returns:
        Full connectivity report with components list
    """
    parsed_blocks = []
    if blocked_edges:
        for edge in blocked_edges:
            parsed_blocks.append((edge["from"], edge["to"]))

    
    all_blocked = BLOCKED_ROADS + parsed_blocks

    uf, report = build_connectivity_map(CITY_GRAPH, all_blocked)
    report["blocked_roads"] = [{"from": u, "to": v} for u, v in all_blocked]
    return report


def check_volunteer_reachability(volunteer_id, disaster_id):
    """
    Check via Union-Find whether a volunteer's location is in the same
    connected component as the disaster location.

    Returns:
        dict with reachability result and reason
    """
    from memory_store import VOLUNTEER_MAP, DISASTER_MAP

    v = VOLUNTEER_MAP.get(volunteer_id)
    d = DISASTER_MAP.get(disaster_id)

    if not v or not d:
        return {"error": "Volunteer or disaster not found."}
    if not v.location:
        return {"error": f"Volunteer {volunteer_id} has no recorded location."}

    result = check_pair_connectivity(
        graph=CITY_GRAPH,
        location_a=v.location,
        location_b=d.location,
        blocked_edges=BLOCKED_ROADS
    )
    result["volunteer_id"] = volunteer_id
    result["disaster_id"] = disaster_id
    return result


def block_road(location_a, location_b):
    """Persist a road blockage for the session (used in disruption simulation)."""
    entry = (location_a, location_b)
    reverse_entry = (location_b, location_a)
    if entry not in BLOCKED_ROADS and reverse_entry not in BLOCKED_ROADS:
        BLOCKED_ROADS.append(entry)
        return True, f"Road {location_a} ↔ {location_b} blocked."
    return False, "Road already blocked."


def unblock_road(location_a, location_b):
    """Remove a road blockage."""
    entry = (location_a, location_b)
    reverse_entry = (location_b, location_a)
    if entry in BLOCKED_ROADS:
        BLOCKED_ROADS.remove(entry)
        return True, f"Road {location_a} ↔ {location_b} restored."
    if reverse_entry in BLOCKED_ROADS:
        BLOCKED_ROADS.remove(reverse_entry)
        return True, f"Road {location_b} ↔ {location_a} restored."
    return False, "Road not found in blocked list."
