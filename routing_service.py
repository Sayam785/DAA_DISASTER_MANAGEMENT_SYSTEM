# services/routing_service.py
# Wraps the Dijkstra engine for use in API endpoints.
# Handles volunteer-to-disaster path computation and nearest volunteer search.

from dijkstra_engine import find_shortest_path, find_nearest_volunteer_location
from graph_engine import CITY_GRAPH, DEHRADUN_LOCATIONS
from memory_store import VOLUNTEER_MAP, DISASTER_MAP

def get_route(volunteer_id, disaster_id):
    """
    Compute the shortest path from a volunteer's location to a disaster site.

    Returns:
        dict with path, distance_km, and coordinate list for Leaflet polyline
    """
    v = VOLUNTEER_MAP.get(volunteer_id)
    d = DISASTER_MAP.get(disaster_id)

    if not v:
        return {"error": f"Volunteer {volunteer_id} not found."}
    if not d:
        return {"error": f"Disaster {disaster_id} not found."}
    if not v.location:
        return {"error": f"Volunteer {volunteer_id} has no recorded city location."}

    volunteer_loc = v.location
    disaster_loc = d.location

    if disaster_loc not in DEHRADUN_LOCATIONS:
        # Attempt to match partial name
        matched = next((k for k in DEHRADUN_LOCATIONS if k.lower() in disaster_loc.lower()), None)
        if matched:
            disaster_loc = matched
        else:
            return {
                "error": f"Disaster location '{disaster_loc}' not found in city graph.",
                "hint": f"Valid locations: {list(DEHRADUN_LOCATIONS.keys())}"
            }

    result = find_shortest_path(volunteer_loc, disaster_loc)
    result["volunteer_id"] = volunteer_id
    result["volunteer_location"] = volunteer_loc
    result["disaster_id"] = disaster_id
    result["disaster_location"] = disaster_loc
    return result


def get_nearest_volunteer_for_disaster(disaster_id):
    """
    Use Dijkstra to identify the closest available volunteer to a given disaster.

    Returns:
        dict with recommended volunteer_id, path, and distance
    """
    d = DISASTER_MAP.get(disaster_id)
    if not d:
        return {"error": f"Disaster {disaster_id} not found."}

    disaster_loc = d.location
    if disaster_loc not in DEHRADUN_LOCATIONS:
        matched = next((k for k in DEHRADUN_LOCATIONS if k.lower() in disaster_loc.lower()), None)
        if not matched:
            return {"error": f"Disaster location '{disaster_loc}' not in city graph."}
        disaster_loc = matched

    # Build map of available volunteers who have a known city location
    available_with_location = {
        v.id: v.location
        for v in VOLUNTEER_MAP.values()
        if v.is_available and v.location and v.location in DEHRADUN_LOCATIONS
    }

    if not available_with_location:
        return {"error": "No available volunteers with known locations found."}

    result = find_nearest_volunteer_location(disaster_loc, available_with_location)
    if not result:
        return {"error": "Could not compute nearest volunteer. Check graph connectivity."}

    result["disaster_id"] = disaster_id
    result["disaster_location"] = disaster_loc
    return result


def get_full_map_data():
    """
    Assemble all data needed to render the Leaflet map:
      - City nodes (all locations with coordinates)
      - City edges (roads)
      - Active disasters (red markers)
      - Volunteer positions (blue markers)
    """
    disasters_on_map = []
    for d in DISASTER_MAP.values():
        if d.status != "Resolved":
            loc_data = DEHRADUN_LOCATIONS.get(d.location)
            if loc_data:
                disasters_on_map.append({
                    "id": d.id,
                    "type": d.type,
                    "severity": d.severity,
                    "location": d.location,
                    "is_emergency": d.is_emergency,
                    "status": d.status,
                    "lat": loc_data["lat"],
                    "lon": loc_data["lon"],
                })

    volunteers_on_map = []
    for v in VOLUNTEER_MAP.values():
        loc_data = DEHRADUN_LOCATIONS.get(v.location)
        if loc_data:
            volunteers_on_map.append({
                "id": v.id,
                "name": v.name,
                "group": v.group,
                "is_available": v.is_available,
                "assigned_to": v.assigned_to,
                "lat": loc_data["lat"],
                "lon": loc_data["lon"],
            })

    graph_data = CITY_GRAPH.to_dict()

    return {
        "disasters": disasters_on_map,
        "volunteers": volunteers_on_map,
        "graph": graph_data,
        "center": {"lat": 30.3254, "lon": 78.0439}
    }
