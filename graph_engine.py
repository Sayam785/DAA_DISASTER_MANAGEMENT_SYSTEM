

DEHRADUN_LOCATIONS = {
    "Clock Tower":       {"lat": 30.3254, "lon": 78.0439},
    "ISBT":              {"lat": 30.3158, "lon": 78.0322},
    "Rajpur Road":       {"lat": 30.3397, "lon": 78.0680},
    "Prem Nagar":        {"lat": 30.3078, "lon": 77.9946},
    "Jakhan":            {"lat": 30.3512, "lon": 78.0735},
    "Sahastradhara":     {"lat": 30.3780, "lon": 78.1120},
    "Ballupur":          {"lat": 30.3290, "lon": 78.0795},
    "Clement Town":      {"lat": 30.2910, "lon": 78.0120},
    "Dalanwala":         {"lat": 30.3189, "lon": 78.0580},
    "Raipur":            {"lat": 30.3630, "lon": 78.0840},
}


CITY_GRAPH_EDGES = [
    ("Clock Tower", "ISBT",          3.2),
    ("Clock Tower", "Rajpur Road",   3.8),
    ("Clock Tower", "Dalanwala",     1.5),
    ("Clock Tower", "Ballupur",      4.1),
    ("ISBT", "Prem Nagar",           5.6),
    ("ISBT", "Clement Town",         6.2),
    ("ISBT", "Dalanwala",            2.8),
    ("Rajpur Road", "Jakhan",        3.3),
    ("Rajpur Road", "Ballupur",      2.5),
    ("Rajpur Road", "Raipur",        5.1),
    ("Jakhan", "Sahastradhara",      5.8),
    ("Jakhan", "Raipur",             3.9),
    ("Sahastradhara", "Raipur",      4.2),
    ("Prem Nagar", "Clement Town",   4.8),
    ("Ballupur", "Dalanwala",        2.9),
    ("Ballupur", "Raipur",           4.6),
    ("Clement Town", "Prem Nagar",   4.8),
    ("Dalanwala", "Rajpur Road",     3.1),
    ("Raipur", "Sahastradhara",      4.2),
]


class CityGraph:
    """
    Represents Dehradun city as a weighted undirected graph.
    Adjacency list implementation for efficient Dijkstra traversal.
    """

    def __init__(self):
        self.adjacency = {}
        self.coordinates = DEHRADUN_LOCATIONS.copy()
        self._build_graph()

    def _build_graph(self):
        for location in DEHRADUN_LOCATIONS:
            self.adjacency[location] = []

        for u, v, weight in CITY_GRAPH_EDGES:
            self.adjacency[u].append((v, weight))
            self.adjacency[v].append((u, weight))  # undirected

    def get_neighbors(self, node):
        return self.adjacency.get(node, [])

    def get_all_nodes(self):
        return list(self.adjacency.keys())

    def get_coordinates(self, location):
        return self.coordinates.get(location, None)

    def add_edge(self, u, v, weight):
        """Allows dynamic edge addition (used for disruption simulation)."""
        if u not in self.adjacency:
            self.adjacency[u] = []
        if v not in self.adjacency:
            self.adjacency[v] = []
        self.adjacency[u].append((v, weight))
        self.adjacency[v].append((u, weight))

    def remove_edge(self, u, v):
        """Simulate road disruption by removing an edge."""
        self.adjacency[u] = [(n, w) for n, w in self.adjacency[u] if n != v]
        self.adjacency[v] = [(n, w) for n, w in self.adjacency[v] if n != u]

    def to_dict(self):
        """Return graph as serializable dict for frontend map rendering."""
        edges = []
        visited = set()
        for u, neighbors in self.adjacency.items():
            for v, w in neighbors:
                key = tuple(sorted([u, v]))
                if key not in visited:
                    visited.add(key)
                    edges.append({"from": u, "to": v, "weight": w})
        return {
            "nodes": [
                {"id": loc, "lat": coords["lat"], "lon": coords["lon"]}
                for loc, coords in self.coordinates.items()
            ],
            "edges": edges
        }


# Singleton graph instance shared across all modules
CITY_GRAPH = CityGraph()
