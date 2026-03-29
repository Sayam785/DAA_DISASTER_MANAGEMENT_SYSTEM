

import heapq
import math
from graph_engine import CITY_GRAPH, DEHRADUN_LOCATIONS


def dijkstra(graph, source):
    """
    Standard Dijkstra implementation using a min-priority-queue (heapq).

    Args:
        graph: CityGraph instance with adjacency list
        source: starting node (string location name)

    Returns:
        dist: dict of shortest distances from source to all nodes
        prev: dict for path reconstruction
    """
    nodes = graph.get_all_nodes()

    dist = {node: float('inf') for node in nodes}
    prev = {node: None for node in nodes}
    dist[source] = 0

    # min-heap: (distance, node)
    min_heap = [(0, source)]

    visited = set()

    while min_heap:
        current_dist, u = heapq.heappop(min_heap)

        if u in visited:
            continue
        visited.add(u)

        for neighbor, weight in graph.get_neighbors(u):
            if neighbor in visited:
                continue
            relaxed = current_dist + weight
            if relaxed < dist[neighbor]:
                dist[neighbor] = relaxed
                prev[neighbor] = u
                heapq.heappush(min_heap, (relaxed, neighbor))

    return dist, prev


def reconstruct_path(prev, source, target):
    """
    Reconstructs the shortest path from source to target
    using the predecessor dictionary from Dijkstra.

    Returns:
        List of location names from source to target (inclusive),
        or empty list if no path exists.
    """
    path = []
    current = target

    while current is not None:
        path.append(current)
        current = prev[current]

    path.reverse()

    # Validate path actually connects source to target
    if not path or path[0] != source:
        return []

    return path


def find_shortest_path(source, target):
    """
    Main function called by the routing service.

    Args:
        source: volunteer's current location
        target: disaster location

    Returns:
        dict with path list, total distance, and coordinates for map rendering
    """
    if source not in CITY_GRAPH.adjacency or target not in CITY_GRAPH.adjacency:
        return {
            "error": f"Location not found in city graph. Check: '{source}' → '{target}'",
            "path": [],
            "distance_km": None,
            "coordinates": []
        }

    if source == target:
        coords = CITY_GRAPH.get_coordinates(source)
        return {
            "path": [source],
            "distance_km": 0,
            "coordinates": [coords] if coords else [],
            "steps": 0
        }

    dist, prev = dijkstra(CITY_GRAPH, source)
    path = reconstruct_path(prev, source, target)

    if not path:
        return {
            "error": f"No path found between '{source}' and '{target}'. Route may be disrupted.",
            "path": [],
            "distance_km": None,
            "coordinates": []
        }

    total_distance = dist[target]

    # Build coordinate list for polyline rendering on Leaflet map
    coordinates = []
    for location in path:
        coords = CITY_GRAPH.get_coordinates(location)
        if coords:
            coordinates.append({"name": location, "lat": coords["lat"], "lon": coords["lon"]})

    return {
        "path": path,
        "distance_km": round(total_distance, 2),
        "coordinates": coordinates,
        "steps": len(path) - 1
    }


def find_nearest_volunteer_location(disaster_location, volunteer_locations):
    """
    Given a disaster location and a list of volunteer locations,
    finds the volunteer with the shortest path using Dijkstra.

    Args:
        disaster_location: string (node name)
        volunteer_locations: dict {volunteer_id: location_name}

    Returns:
        dict with nearest volunteer id, distance, and path
    """
    if not volunteer_locations:
        return None

    best_volunteer = None
    best_distance = float('inf')
    best_path_data = None

    dist_from_disaster, prev_from_disaster = dijkstra(CITY_GRAPH, disaster_location)

    for vol_id, vol_location in volunteer_locations.items():
        if vol_location not in CITY_GRAPH.adjacency:
            continue

        d = dist_from_disaster.get(vol_location, float('inf'))
        if d < best_distance:
            best_distance = d
            best_volunteer = vol_id

            path = reconstruct_path(prev_from_disaster, disaster_location, vol_location)
            path.reverse()  # volunteer → disaster direction

            coordinates = []
            for loc in path:
                coords = CITY_GRAPH.get_coordinates(loc)
                if coords:
                    coordinates.append({"name": loc, "lat": coords["lat"], "lon": coords["lon"]})

            best_path_data = {
                "volunteer_id": vol_id,
                "path": path,
                "distance_km": round(best_distance, 2),
                "coordinates": coordinates
            }

    return best_path_data
